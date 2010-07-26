def site_code_from_patient_id(id):
    id = id.strip()
    if id is None or len(id)<7:
        raise ValueError
    return id[:5]

