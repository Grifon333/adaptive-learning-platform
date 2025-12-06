import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import cast

from fastapi import BackgroundTasks, Depends, FastAPI, HTTPException, status
from loguru import logger
from sqlalchemy import func
from sqlalchemy.orm import Session

from src import models, schemas, security
from src.database import get_db
from src.logger import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("User service initializing...")
    yield
    # Shutdown
    logger.info("User service shutting down...")


setup_logging()
app = FastAPI(title="User Service", lifespan=lifespan)


def get_current_user(
    token: str = Depends(security.oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    """
    Decodes the token, finds the user in the database, and returns it.
    This protects endpoints.
    """
    token_data = security.decode_access_token(token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token_data.token_type != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type, expected 'access'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token_data.user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(models.User).filter(models.User.id == token_data.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    return cast(models.User, user)


def send_verification_email(email: str, token: str):
    # In production, use e.g., FastMail, AWS SES, or SendGrid here
    logger.info(f"[Background Task] Sending verification email to {email}. Link: /verify?token={token}")


@app.post("/api/v1/auth/register", status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # 1. Check existing
    if db.query(models.User).filter(models.User.email == user.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")

    # 2. Create User
    new_user = models.User(
        email=user.email,
        password_hash=security.get_password_hash(user.password),
        first_name=user.first_name,
        last_name=user.last_name,
        role=models.UserRole.student,
        is_verified=False,
    )

    # 3. Create Profile
    db.add(new_user)
    db.flush()  # Generate ID

    new_profile = models.StudentProfile(user_id=new_user.id)
    db.add(new_profile)
    db.commit()
    db.refresh(new_user)

    # 4. Trigger Email Verification
    verification_token = security.create_verification_token(new_user.email)
    background_tasks.add_task(send_verification_email, new_user.email, verification_token)

    return {"message": "User registered. Please check your email to verify account."}


@app.post("/api/v1/auth/verify-email")
def verify_email(req: schemas.EmailVerificationRequest, db: Session = Depends(get_db)):
    email = security.decode_token(req.token, "verification")
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.is_verified:
        return {"message": "Email already verified"}

    user.is_verified = True
    db.commit()
    return {"message": "Email verified successfully"}


@app.post("/api/v1/auth/social-login", response_model=schemas.Token)
def social_login(login_data: schemas.UserSocialLogin, db: Session = Depends(get_db)):
    """
    Handles login/registration from Social Providers.
    Assumes Frontend has already verified validity with Provider and sends clean data.
    """
    user = db.query(models.User).filter(models.User.email == login_data.email).first()

    if not user:
        # Register on the fly
        user = models.User(
            email=login_data.email,
            first_name=login_data.first_name,
            last_name=login_data.last_name,
            provider=login_data.provider,
            provider_id=login_data.provider_id,
            is_verified=True,  # Social accounts are implicitly verified
            role=models.UserRole.student,
            avatar_url=login_data.avatar_url,
        )
        db.add(user)
        db.flush()
        db.add(models.StudentProfile(user_id=user.id))
        db.commit()
        db.refresh(user)
        logger.info(f"New Social User Registered: {user.email}")
    else:
        # Link provider if not linked (Optional logic)
        if not user.provider:
            user.provider = login_data.provider
            user.provider_id = login_data.provider_id
            db.commit()

    # Generate Session
    subject = {"sub": str(user.id)}
    return {
        "access_token": security.create_access_token(subject),
        "refresh_token": security.create_refresh_token(subject),
        "token_type": "bearer",
    }


@app.post("/api/v1/auth/forgot-password")
def forgot_password(req: schemas.PasswordResetRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == req.email).first()
    if user:
        # Security: Don't reveal if user exists or not, but log internally
        token = security.create_password_reset_token(user.email)
        logger.info(f"[EVENT: email_send] Password Reset for {user.email}: {token}")

    return {"message": "If the email exists, a reset link has been sent."}


@app.post("/api/v1/auth/reset-password")
def reset_password(req: schemas.PasswordResetConfirm, db: Session = Depends(get_db)):
    email = security.decode_token(req.token, "reset")
    if not email:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.password_hash = security.get_password_hash(req.new_password)
    db.commit()
    return {"message": "Password updated successfully"}


@app.post("/api/v1/auth/login", response_model=schemas.Token)
def login_for_access_token(
    user_credentials: schemas.UserLogin,
    db: Session = Depends(get_db),
):
    """
    Logs in a user and returns an access token.
    """
    cred_email = user_credentials.email
    cred_password = user_credentials.password
    logger.info(f"Logging in user: {cred_email}")

    if not cred_email or not cred_password:
        logger.error("Email and password are required")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Email and password are required",
        )

    db_user = db.query(models.User).filter(models.User.email == cred_email).first()

    if not db_user:
        logger.error(f"Failed to log in: {cred_email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    assert isinstance(db_user.password_hash, str)
    if not security.verify_password(cred_password, db_user.password_hash):
        logger.error(f"Failed to log in: {cred_email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Creating a JWT token
    subject_data = {"sub": str(db_user.id)}
    access_token = security.create_access_token(data=subject_data)
    refresh_token = security.create_refresh_token(data=subject_data)

    # Updating the last login time
    db_user.last_login = func.now()
    db.commit()

    logger.success(f"User successfully logged in: {db_user.email}")
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@app.get("/api/v1/users/me/profile", response_model=schemas.FullUserProfile)
def get_user_profile(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Returns the unified profile (Identity + Learning Data).
    """
    if current_user.profile is None:
        logger.warning(f"Profile missing for user {current_user.id}. Auto-healing...")

        # 1. Create new profile instance (Initializes S_0^u components with defaults)
        new_profile = models.StudentProfile(user_id=current_user.id)

        # 2. Persist to DB
        try:
            db.add(new_profile)
            db.commit()
            # 3. Refresh the user to load the relationship 'profile'
            db.refresh(current_user)
        except Exception as e:
            logger.error(f"Failed to auto-heal profile: {e}")
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to initialize user profile"
            ) from e

    # At this point, current_user.profile is guaranteed to exist
    profile = current_user.profile

    if profile is None:
        return schemas.FullUserProfile(
            id=current_user.id,
            email=cast(str, current_user.email),
            first_name=cast(str, current_user.first_name),
            last_name=cast(str, current_user.last_name),
            avatar_url=current_user.avatar_url,
            role=str(current_user.role),
            cognitive_profile={},
            learning_preferences={},
            learning_goals=[],
            study_schedule={},
            timezone=None,
            privacy_settings={},
        )

    # Manual mapping to flatten the structure for the schema
    return schemas.FullUserProfile(
        # Identity
        id=current_user.id,
        email=cast(str, current_user.email),
        first_name=cast(str, current_user.first_name),
        last_name=cast(str, current_user.last_name),
        avatar_url=current_user.avatar_url,
        role=str(current_user.role),
        # Profile Data (psi_u)
        cognitive_profile=profile.cognitive_profile or {},
        learning_preferences=profile.learning_preferences or {},
        learning_goals=profile.learning_goals or [],
        study_schedule=profile.study_schedule or {},
        timezone=profile.timezone,
        privacy_settings=profile.privacy_settings or {},
    )


@app.put("/api/v1/users/me/profile", response_model=schemas.FullUserProfile)
def update_user_profile(
    profile_data: schemas.UserProfileUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Updates user identity and learning profile.
    """
    profile = current_user.profile
    if profile is None:
        raise HTTPException(status_code=404, detail="Student profile not found")

    # 1. Update Identity Fields (User Table)
    if profile_data.first_name:
        current_user.first_name = profile_data.first_name
    if profile_data.last_name:
        current_user.last_name = profile_data.last_name
    if profile_data.avatar_url:
        current_user.avatar_url = profile_data.avatar_url

    # 2. Update Profile Fields (StudentProfile Table)
    if profile_data.learning_preferences is not None:
        profile.learning_preferences = profile_data.learning_preferences
    if profile_data.learning_goals is not None:
        profile.learning_goals = profile_data.learning_goals
    if profile_data.study_schedule is not None:
        profile.study_schedule = profile_data.study_schedule
    if profile_data.timezone is not None:
        profile.timezone = profile_data.timezone
    if profile_data.privacy_settings is not None:
        profile.privacy_settings = profile_data.privacy_settings

    db.add(current_user)
    db.add(profile)
    db.commit()
    db.refresh(current_user)

    # Return updated structure
    return schemas.FullUserProfile(
        id=current_user.id,
        email=cast(str, current_user.email),
        first_name=cast(str, current_user.first_name),
        last_name=cast(str, current_user.last_name),
        avatar_url=current_user.avatar_url,
        role=str(current_user.role),
        cognitive_profile=current_user.profile.cognitive_profile or {},
        learning_preferences=current_user.profile.learning_preferences or {},
        learning_goals=current_user.profile.learning_goals or [],
        study_schedule=current_user.profile.study_schedule or {},
        timezone=current_user.profile.timezone,
        privacy_settings=current_user.profile.privacy_settings or {},
    )


@app.post(
    "/api/v1/learning-paths",
    response_model=schemas.LearningPath,
    status_code=status.HTTP_201_CREATED,
)
def create_learning_path(
    path_data: schemas.LearningPathCreate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Creates a new learning path for the currently authenticated student.
    """
    logger.info(f"Creating learning path for user {current_user.email}")

    try:
        # 1. Archive old paths for the same goal(s)
        # Assume that if the goal is the same, then this is a trajectory update.
        # path_data.goal_concepts - list of target IDs.

        # Find active paths for this student
        active_paths = (
            db.query(models.LearningPath)
            .filter(
                models.LearningPath.student_id == current_user.id,
                models.LearningPath.status == "active",
            )
            .all()
        )

        for existing_path in active_paths:
            # Check whether the goals intersect (is this the path to the same goal?)
            existing_goals = set(existing_path.goal_concepts)
            new_goals = set(path_data.goal_concepts)

            if not existing_goals.isdisjoint(new_goals):
                logger.info(f"Archiving old path {existing_path.id} (Goal overlap)")
                existing_path.status = "archived"  # type: ignore
                db.add(existing_path)

        # Committing updates to old paths before creating new one
        db.commit()

        # 2. Creating the main LearningPath record
        db_path = models.LearningPath(
            student_id=current_user.id,
            goal_concepts=path_data.goal_concepts,
            estimated_time=path_data.estimated_time,
            status="active",  # Explicitly active
        )
        db.add(db_path)

        # Flush to get the ID
        db.flush()

        # 3. Creating steps (LearningStep)
        db_steps = []
        for step_data in path_data.steps:
            db_step = models.LearningStep(
                path_id=db_path.id,  # Using ID after flush
                step_number=step_data.step_number,
                concept_id=step_data.concept_id,
                resources=step_data.resources,
                estimated_time=step_data.estimated_time,
                difficulty=step_data.difficulty,
                status=step_data.status,
                is_remedial=step_data.is_remedial,
                description=step_data.description,
            )
            db_steps.append(db_step)
        db.add_all(db_steps)

        db.commit()
        db.refresh(db_path)

        logger.success(f"Learning path {db_path.id} created successfully.")
        return db_path

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to create learning path: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create learning path: {str(e)}",
        ) from e


@app.post("api/v1/auth/refresh", response_model=schemas.Token)
def refresh_access_token(refresh_request: schemas.TokenRefresh, db: Session = Depends(get_db)):
    """
    Update the Access Token, using the Refresh Token
    """
    token_data = security.decode_access_token(refresh_request.refresh_token)
    if token_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if token_data.token_type != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type, expected 'refresh'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check user existing
    user = db.query(models.User).filter(models.User.id == token_data.user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token signature or user not found",
        )

    # Generate a new pair of tokens
    subject_data = {"sub": str(user.id)}
    new_access_token = security.create_access_token(data=subject_data)
    new_refresh_token = security.create_refresh_token(data=subject_data)

    logger.info(f"Token refreshed for user: {user.email}")
    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }


@app.get(
    "/api/v1/students/{student_id}/learning-paths",
    response_model=list[schemas.LearningPath],
)
def get_student_paths(
    student_id: str,  # UUID str
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if str(current_user.id) != student_id:
        raise HTTPException(status_code=403, detail="Not authorized to view these paths")
    # Filter: return only ACTIVE or COMPLETED.
    # ARCHIVED hide.
    paths = (
        db.query(models.LearningPath)
        .filter(
            models.LearningPath.student_id == student_id,
            models.LearningPath.status.in_(["active", "completed"]),
        )
        .order_by(models.LearningPath.created_at.desc())
        .all()
    )
    return paths


@app.patch(
    "/api/v1/learning-paths/steps/{step_id}/progress",
    status_code=status.HTTP_204_NO_CONTENT,
)
def update_step_progress(
    step_id: uuid.UUID,
    update_data: schemas.StepProgressUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Heartbeat endpoint. Updates the actual_time spent on a specific step
    and aggregates it to the parent LearningPath.
    """
    # 1. Fetch Step with Path to verify ownership
    step = (
        db.query(models.LearningStep)
        .join(models.LearningPath)
        .filter(models.LearningStep.id == step_id)
        .filter(models.LearningPath.student_id == current_user.id)
        .first()
    )

    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning step not found or access denied",
        )

    # 2. Update Step Time
    current_step_time = step.actual_time or 0
    step.actual_time = current_step_time + update_data.time_delta  # type: ignore[assignment]

    # 3. Update Status to 'in_progress' if it was pending
    if step.status == "pending":
        step.status = "in_progress"  # type: ignore[assignment]
        step.started_at = datetime.now(UTC)  # type: ignore[assignment]

    # 4. Update Parent Path Time
    # We load the path relationship
    path = step.path
    current_path_time = path.actual_time or 0
    path.actual_time = current_path_time + update_data.time_delta
    path.updated_at = datetime.now(UTC)

    db.commit()
    return None


@app.post(
    "/api/v1/learning-paths/steps/{step_id}/complete",
    response_model=schemas.StepCompleteResponse,
)
def complete_step(
    step_id: uuid.UUID,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Marks a step as completed. Recalculates the overall path completion percentage.
    """
    # 1. Fetch Step and Path
    step = (
        db.query(models.LearningStep)
        .join(models.LearningPath)
        .filter(models.LearningStep.id == step_id)
        .filter(models.LearningPath.student_id == current_user.id)
        .first()
    )

    if not step:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Learning step not found or access denied",
        )

    # 2. Update Step Status
    if step.status != "completed":
        step.status = "completed"  # type: ignore[assignment]
        step.completed_at = datetime.now(UTC)  # type: ignore[assignment]

    # 3. Recalculate Path Statistics
    path = step.path

    # Count total and completed steps
    # We use db.query to ensure we count all steps, not just loaded ones
    total_steps = (
        db.query(func.count(models.LearningStep.id)).filter(models.LearningStep.path_id == path.id).scalar()
    ) or 1

    completed_steps = (
        db.query(func.count(models.LearningStep.id))
        .filter(models.LearningStep.path_id == path.id)
        .filter(models.LearningStep.status == "completed")
        .scalar()
    ) or 0

    completion_percentage = round(completed_steps / total_steps, 2)
    path.completion_percentage = completion_percentage
    path.updated_at = datetime.now(UTC)

    # 4. Check for Path Completion
    path_is_completed = False
    if completion_percentage >= 1.0:
        path.status = "completed"
        path.completed_at = datetime.now(UTC)
        path_is_completed = True
        logger.info(f"User {current_user.id} completed path {path.id}!")

    db.commit()

    return schemas.StepCompleteResponse(
        step_id=cast(uuid.UUID, step.id),
        status="completed",
        path_completion_percentage=completion_percentage,
        path_is_completed=path_is_completed,
    )


@app.post(
    "/api/v1/learning-paths/steps/{step_id}/quiz-result",
    response_model=schemas.StepCompleteResponse,
)
def update_step_quiz_result(
    step_id: uuid.UUID,
    result: schemas.StepQuizUpdate,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Updates the step with quiz results.
    If passed, marks as completed and recalculates path progress.
    """
    step = (
        db.query(models.LearningStep)
        .join(models.LearningPath)
        .filter(models.LearningStep.id == step_id)
        .filter(models.LearningPath.student_id == current_user.id)
        .first()
    )

    if not step:
        raise HTTPException(status_code=404, detail="Step not found")

    # 1. Update Score
    step.score = result.score  # type: ignore[assignment]

    # 2. Handle Completion (only if passed)
    if result.passed:
        if step.status != "completed":
            step.status = "completed"  # type: ignore[assignment]
            step.completed_at = datetime.now(UTC)  # type: ignore[assignment]

    # 3. Recalculate Path Stats (Common logic with complete_step)
    path = step.path
    total_steps = (
        db.query(func.count(models.LearningStep.id)).filter(models.LearningStep.path_id == path.id).scalar()
    ) or 1

    completed_steps = (
        db.query(func.count(models.LearningStep.id))
        .filter(models.LearningStep.path_id == path.id)
        .filter(models.LearningStep.status == "completed")
        .scalar()
    ) or 0

    path.completion_percentage = round(completed_steps / total_steps, 2)
    path.updated_at = datetime.now(UTC)

    # Check for full path completion
    path_is_completed = False
    if path.completion_percentage >= 1.0:
        path.status = "completed"
        path.completed_at = datetime.now(UTC)
        path_is_completed = True

    db.commit()

    return schemas.StepCompleteResponse(
        step_id=cast(uuid.UUID, step.id),
        status=cast(str, step.status),
        path_completion_percentage=path.completion_percentage,
        path_is_completed=path_is_completed,
    )


@app.post(
    "/api/v1/learning-paths/{path_id}/adapt",
    response_model=schemas.AdaptationResponse,
    status_code=status.HTTP_200_OK,
)
def adapt_learning_path(
    path_id: uuid.UUID,
    request: schemas.AdaptationRequest,
    db: Session = Depends(get_db),
):
    """
    Transactional operation to:
    1. Shift existing steps down.
    2. Insert remedial steps.
    3. Log adaptation history.
    """
    logger.info(f"Adapting path {path_id} due to {request.trigger_type}")

    try:
        # 1. Shift steps
        # We move all steps >= insert_at_step by the number of new steps
        shift_amount = len(request.new_steps)

        # Note: We must execute this update carefully to avoid unique constraint violations on (path_id, step_number).
        # We sort descending to shift the last ones first if doing row-by-row,
        # but SQL UPDATE handles this set-based operation safely usually.
        # Ideally, we temporarily disable the constraint or update using a negative logic if needed,
        # but simpler is:

        db.query(models.LearningStep).filter(
            models.LearningStep.path_id == path_id,
            models.LearningStep.step_number >= request.insert_at_step,
        ).update(
            {models.LearningStep.step_number: models.LearningStep.step_number + shift_amount},
            synchronize_session=False,
        )

        # 2. Insert New Steps
        new_db_steps = []
        current_num = request.insert_at_step
        for step_data in request.new_steps:
            new_step = models.LearningStep(
                id=uuid.uuid4(),
                path_id=path_id,
                step_number=current_num,
                concept_id=step_data.concept_id,
                resources=step_data.resources,
                estimated_time=step_data.estimated_time,
                difficulty=step_data.difficulty,
                status="pending",
                is_remedial=True,  # Explicitly mark as remedial
                description=step_data.description,
            )
            new_db_steps.append(new_step)
            current_num += 1

        db.add_all(new_db_steps)

        # 3. Log History
        adaptation_log = models.Adaptation(
            path_id=path_id,
            trigger_type=request.trigger_type,
            strategy_applied=request.strategy,
            changes={"inserted_count": shift_amount, "at_step": request.insert_at_step},
        )
        db.add(adaptation_log)

        db.commit()
        return {
            "success": True,
            "message": "Path adapted successfully",
            "path_id": path_id,
        }

    except Exception as e:
        db.rollback()
        logger.error(f"Failed to adapt path: {e}")
        raise HTTPException(status_code=500, detail="Adaptation failed") from e


@app.get("/api/v1/learning-paths/steps/{step_id}", response_model=schemas.LearningStep)
def get_learning_step(
    step_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    step = db.query(models.LearningStep).filter(models.LearningStep.id == step_id).first()
    if not step:
        raise HTTPException(status_code=404, detail="Step not found")
    return step
