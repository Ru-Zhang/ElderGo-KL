from pydantic import BaseModel


class TravelPreferences(BaseModel):
    # Defaults represent neutral scoring (no strict priority selected).
    accessibility_first: bool = False
    least_walk: bool = False
    fewest_transfers: bool = False
