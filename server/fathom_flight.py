import datetime
import calendar
class Flight():
    def __init__(self, name):
        """Return a Customer object whose name is *name* and starting
        balance is *balance*."""
        self.name = name
        name_objects = name.split('_')
        month = int(name_objects[0])
        day = name_objects[1]
        hour = name_objects[2]
        minute = name_objects[3]

        latitude = 0
        longitude = 0
        # check if lat and long are present
        if len(name_objects) > 6:
            latitude = name_objects[5]
            long_objects = name_objects[6].split('.')
            longitude = long_objects[0]
            if len(long_objects)>2:
                longitude += "."+long_objects[1]

        self.full_time = str(month)+"-"+str(day)+"_"+str(hour)+"_"+str(minute)
        self.when = str(calendar.month_abbr[month])+" "+str(day)
        self.start_time = ""+hour+":"+minute
        self.latitude = latitude
        self.longitude = longitude
        self.isConverted = self.name.endswith(".mp4")







    def serialize(self):
        return {
            'name': self.name,
            'when': self.when,
            'start_time': self.start_time,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'full_time': self.full_time,
            'converted': self.isConverted
        }
