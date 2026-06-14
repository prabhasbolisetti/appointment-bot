from app.repositories import slot_repo


def get_slot(slot_id: str):
    return slot_repo.get_slot(slot_id)


def get_slots_by_clinic(clinic_id: str, slot_date: str = None, status: str = None):
    return slot_repo.get_slots_by_clinic(clinic_id, slot_date, status)


def bulk_create_slots(
    clinic_id: str,
    start_date,
    end_date,
    open_time,
    close_time,
    slot_duration_minutes: int,
):
    return slot_repo.bulk_create_slots(
        clinic_id,
        start_date,
        end_date,
        open_time,
        close_time,
        slot_duration_minutes,
    )


def delete_slot(slot_id: str):
    return slot_repo.delete_slot(slot_id)


def release_slot(slot_id: str):
    return slot_repo.release_slot(slot_id)