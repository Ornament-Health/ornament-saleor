import logging
from ftplib import FTP, all_errors
from django.conf import settings
from django.core.management.base import BaseCommand


logger = logging.getLogger(__name__)


XML_OUTPUT_DIR = "/Output"
PDF_OUTPUT_DIR = "/OutputPDF"
XML_IGNORE_DIR = f"{XML_OUTPUT_DIR}Ignore"
PDF_IGNORE_DIR = f"{PDF_OUTPUT_DIR}Ignore"

FTP_COUNTDOWN_REFERENCE = 5
FTP_PORTION_REFERENCE = 500


class Command(BaseCommand):
    help = "Cleanup KDL FTP server *Ignore directories."

    def get_ftp(self, dir, ftp=None):
        ftp and ftp.close()
        ftp = FTP(
            settings.KDL_FTP_HOST, settings.KDL_FTP_LOGIN, settings.KDL_FTP_PASSWORD
        )
        ftp.cwd(dir)
        return ftp

    def handle(self, *args, **options):
        logger.info("KDL: FTP cleanup starting...")

        print("FTP *Ignore directories cleanup.")
        print("Directories for cleaning up:")
        print(f"    {XML_IGNORE_DIR}\n    {PDF_IGNORE_DIR}")

        for dir in (XML_IGNORE_DIR, PDF_IGNORE_DIR):
            print(f'\nCleaning up "{dir}":')

            ftp = self.get_ftp(dir)
            files = ftp.nlst()

            print(f"Files for erasing: {len(files)}.")

            portion = FTP_PORTION_REFERENCE
            terminate = False
            print(f"Files deletion log:")
            while files:
                countdown = FTP_COUNTDOWN_REFERENCE
                while True:
                    try:
                        file = files[0]
                        ftp.delete(file)
                        files.pop(0)
                        print(f"{len(files):>8}: {dir}/{file} ")
                    except all_errors as e:
                        countdown -= 1
                        if countdown:
                            ftp = self.get_ftp(dir, ftp)
                            print(
                                f"{len(files):>8}: {dir}/{file}   >>> COUNTDOWN -1 ({countdown})"
                            )
                            continue
                        terminate = True
                        print(f"{len(files):>8}: {dir}/{file}   >>> COUNTDOWN ERROR")
                        break
                    break
                if terminate:
                    print(f"{len(files):>8}: {dir}   >>> COUNTDOWN TERMINATE")
                    break

                portion -= 1
                if not portion:
                    print(f"{len(files):>8}: {dir}   >>> PORTION RECONNECT")
                    portion = FTP_PORTION_REFERENCE
                    ftp = self.get_ftp(dir, ftp)

        logger.info("KDL: FTP cleanup finished.")
