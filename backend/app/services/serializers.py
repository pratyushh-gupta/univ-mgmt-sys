def user_json(u):
    return {"id": u.id, "user_id": u.user_id, "name": u.name, "email": u.email,
            "role": u.role, "department": u.department, "semester": u.semester}

