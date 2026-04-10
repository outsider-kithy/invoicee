import sys
sys.path.insert(0,"/var/www/invoicee")
from app import create_app
application = create_app()
