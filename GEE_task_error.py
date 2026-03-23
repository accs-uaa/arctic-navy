# Import packages
import ee

# Define paths
ee_project = 'akveg-map'

# Authenticate Earth Engine
print('Connecting to Earth Engine server...')
try:
    ee.Initialize(project=ee_project)
except Exception as e:
    print('Prompting authentication...')
    ee.Authenticate()
    ee.Initialize(project=ee_project)

task_id = '3L2TSEE5YUMBORMUPH3E6Z64'
status = ee.data.getTaskStatus(task_id)[0]

if status['state'] == 'FAILED':
    print(f"{status['error_message']}")