def user_json(user):
    profile = user.student_profile if user.role == "student" else user.faculty_profile if user.role == "faculty" else None
    department = profile.department.name if profile else None
    semester = profile.semester.number if user.role == "student" and profile and profile.semester else None
    return {
        "id": user.id,
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "is_active": user.is_active,
        "department": department,
        "department_id": profile.department_id if profile else None,
        "semester": semester,
        "student_id": profile.id if user.role == "student" and profile else None,
        "faculty_id": profile.id if user.role == "faculty" and profile else None,
    }

