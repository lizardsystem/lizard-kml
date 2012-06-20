#include <string.h>
#include <stdio.h>
#include <stdlib.h>
#include "netcdf.h"

void handle_error(int status) {
     if (status != NC_NOERR) {
        fprintf(stderr, "%s\n", nc_strerror(status));
        exit(-1);
        }
     }
int main() {
  const char *path = "http://opendap.tudelft.nl/thredds/dodsC/data2/deltares/rijkswaterstaat/jarkus/profiles/transect.nc";
  int ncid;
  int status;
  status = nc_open (path, 0, &ncid);
  if (status != NC_NOERR) handle_error(status);
  // Get the lat variable
  int lat_id;
  status = nc_inq_varid (ncid, "lat", &lat_id);
  if (status != NC_NOERR) handle_error(status);

  // Get one element element of the 2d array lat
  static size_t start0[] = {0, 0}; /* start at first value */
  static size_t start1[] = {1, 1}; /* start at second value */
  static size_t count[] = {1, 1}; /* get one value*/
  double vals[1*1];   /* array to hold values */

  // Read the second value (takes a jiffy)
  status = nc_get_vara(ncid, lat_id, start1, count, vals);
  if (status != NC_NOERR) handle_error(status);
  printf("lat[1,1]:%f\n", vals[0]);

  // Takes very long (reads the whole lat array)
  status = nc_get_vara(ncid, lat_id, start0, count, vals);
  if (status != NC_NOERR) handle_error(status);
  printf("lat[0,0] read 1x1:%f\n", vals[0]);

  status = nc_close(ncid);
  if (status != NC_NOERR) handle_error(status);

  return 0;
}
