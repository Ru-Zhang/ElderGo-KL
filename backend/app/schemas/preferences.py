from pydantic import BaseModel


class TravelPreferences(BaseModel):
    accessibility_first: bool = False
    least_walk: bool = False
    fewest_transfers: bool = False
