SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;
SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;
SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='TRADITIONAL';

use photoshare;

INSERT INTO Users VALUES (1, "M", "ssss@bu.edu", "123456", DATE "2017-10-24", "Boston", "Donald", "Trump");
INSERT INTO Album VALUES (1, "Test Album 1", 1, DATE "2017-10-24");
INSERT INTO Album VALUES (2, "Test Album 2", 1, DATE "2017-10-24");
INSERT INTO Users VALUES (2, "M", "aaaa@bu.edu", "123456", DATE "2017-10-24", "Boston", "Barack", "Obama");
INSERT INTO Album VALUES (3, "Test Album 1", 2, DATE "2017-10-24");
INSERT INTO Album VALUES (4, "Test Album 2", 2, DATE "2017-10-24");