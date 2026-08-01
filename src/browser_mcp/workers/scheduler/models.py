from pydantic import BaseModel
class ScheduleDefinition(BaseModel):
    name:str; cron:str; payload:dict[str,object]
