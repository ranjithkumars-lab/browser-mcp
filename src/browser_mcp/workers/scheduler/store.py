from browser_mcp.workers.scheduler.models import ScheduleDefinition
class ScheduleStore:
    def __init__(self)->None:self._items:dict[str,ScheduleDefinition]={}
    def put(self,item:ScheduleDefinition)->None:self._items[item.name]=item
    def all(self)->list[ScheduleDefinition]:return list(self._items.values())
