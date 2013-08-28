import os

from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    args = '[nothing]'
    help = 'Synchronizes all Jarkus NETCDF files to a local mirror directory.'

    def handle(self, *args, **options):
        if not os.path.isdir(settings.NC_RESOURCE_LOCAL_DIR):
            print 'Creating {0}'.format(settings.NC_RESOURCE_LOCAL_DIR)
            os.mkdir(settings.NC_RESOURCE_LOCAL_DIR)
        for nc_name, opendap_url in settings.NC_RESOURCE_URLS.items():
            file_path = os.path.join(settings.NC_RESOURCE_LOCAL_DIR, nc_name + '.nc')
            http_url = opendap_url.replace('/dodsC/', '/fileServer/')
            cmd = '''wget --output-document="{0}" --no-directories --ignore-length --mirror "{1}"'''.format(file_path, http_url)
            print 'Executing {0}'.format(cmd)
            os.system(cmd)
        print 'All done'
