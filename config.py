"""Central settings used across the project."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'emp.db')
SECRET_KEY = 'emp-dev-secret-change-me'

EXAM_TYPES = ['Viva', 'Practical', 'Project Demo', 'Assessment']
EXAM_STATUS = ['Draft', 'Slot Creation', 'Booking Open', 'Closed', 'Completed']
