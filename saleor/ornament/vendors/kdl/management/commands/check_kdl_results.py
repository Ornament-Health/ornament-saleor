import logging
from django.conf import settings
from django.core.management.base import BaseCommand
from saleor.ornament.vendors.kdl.tasks import check_for_new_results
from saleor.utils.files import FileLockedException, FileLock


logger = logging.getLogger(__name__)

KDL_CHECK_RESULT_LOCK_TIMEOUT = 60 * 15
KDL_CHECK_RESULT_LOCK_FILENAME = "kdl_check_results.lock"


class Command(BaseCommand):
    help = "Check results on KDL FTP server and upload new PDF files to Imageset API"

    def handle(self, *args, **options):
        try:
            locker = None  # init variable
            locker = FileLock(
                settings.LOCK_DIR,
                locktime=KDL_CHECK_RESULT_LOCK_TIMEOUT,
                lockname=KDL_CHECK_RESULT_LOCK_FILENAME,
            )
            if not locker.lock():
                raise FileLockedException
            logger.debug(
                "KDL: Check results locked for {}".format(locker.check(astime=True))
            )

            check_for_new_results()
        except FileLockedException as e:
            logger.debug(
                "KDL: Check results is already locked for ({})".format(
                    locker.check(astime=True)
                )
            )
            locker = None
        finally:
            if locker:
                logger.debug(
                    "KDL: Check results unlocked after {}".format(
                        locker.check(astime=True, remained=False)
                    )
                )
                locker.unlock()
