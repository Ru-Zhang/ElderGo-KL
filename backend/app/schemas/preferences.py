from pydantic import BaseModel


class TravelPreferences(BaseModel):
    # ElderGo defaults: less walking and accessibility; transfers are lowest priority.
    accessibility_first: bool = True
    least_walk: bool = True
    fewest_transfers: bool = False
