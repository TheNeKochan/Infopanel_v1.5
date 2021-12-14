import os
import base64

resources_names = [
    "ITSchool.png",
    "Logo_L.png",
    "lyceum.png",
    "minobrnso.png",
    "minobrnso.png",
    "schedule.png",
    "proxy.exe",
    "Rasp.db"
]
for i in resources_names:
    if not os.path.exists(i):
        import resources
        for resource in resources.resources.items():
            open(resource[0], 'wb').write(base64.b64decode(resource[1]))
        del resources.resources
        del resources
