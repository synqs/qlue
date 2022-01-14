"""
The module that contains all the necessary logic for communication with the external
storage for the jobs.
"""
from abc import ABC
import sys
from typing import List

import dropbox
from dropbox.files import WriteMode
from dropbox.exceptions import ApiError, AuthError
from decouple import config


class StorageProvider(ABC):
    """
    The template for accessing any storage providers like dropbox, amazon S3 etc.
    """

    def upload(self, dump_str: str, storage_path: str) -> None:
        """
        Upload the file to the storage
        """

    def get_file_content(self, storage_path: str) -> str:
        """
        Get the file content from the storage
        """

    def get_file_queue(self, storage_path: str) -> List[str]:
        """
        Get a list of files
        """

    def move_file(self, start_path: str, final_path: str) -> None:
        """
        Move the file from start_path to `final_path`
        """


class DropboxProvider(StorageProvider):
    """
    The access to the dropbox
    """

    # Add OAuth2 access token here.
    # You can generate one for yourself in the App Console.
    # <https://blogs.dropbox.com/developers/2014/05/generate-an-access-token-for-your-own-account/>
    def __init__(self):
        """
        Set up the neccessary keys.
        """
        self.app_key = config("APP_KEY")
        self.refresh_token = config("REFRESH_TOKEN")

    def upload(self, dump_str: str, storage_path: str) -> None:
        """
        Upload the file identified to the dropbox
        """
        # Create an instance of a Dropbox class, which can make requests to the API.
        with dropbox.Dropbox(
            oauth2_refresh_token=self.refresh_token, app_key=self.app_key
        ) as dbx:
            # Check that the access token is valid
            dbx.users_get_current_account()
            dbx.files_upload(
                dump_str.encode("utf-8"), storage_path, mode=WriteMode("overwrite")
            )

    def get_file_content(self, storage_path: str) -> str:
        """
        Get the file content from the dropbox
        """
        # Create an instance of a Dropbox class, which can make requests to the API.
        with dropbox.Dropbox(
            oauth2_refresh_token=self.refresh_token, app_key=self.app_key
        ) as dbx:
            # Check that the access token is valid
            try:
                dbx.users_get_current_account()
            except AuthError:
                sys.exit("ERROR: Invalid access token.")
            # We should really handle these exceptions cleaner, but this seems a bit
            # complicated right now
            # pylint: disable=W0703
            try:
                _, res = dbx.files_download(path=storage_path)
                data = res.content
            except Exception as err:
                sys.exit(err)
        return data.decode("utf-8")

    def get_file_queue(self, storage_path: str) -> List[str]:
        """
        Get a list of files
        """

        # Create an instance of a Dropbox class, which can make requests to the API.
        with dropbox.Dropbox(
            oauth2_refresh_token=self.refresh_token, app_key=self.app_key
        ) as dbx:
            # Check that the access token is valid
            try:
                dbx.users_get_current_account()
            except AuthError:
                sys.exit("ERROR: Invalid access token.")
            # We should really handle these exceptions cleaner, but this seems a bit
            # complicated right now
            # pylint: disable=W0703
            try:
                response = dbx.files_list_folder(path=storage_path)
                file_list = response.entries
                file_list = [item.name for item in file_list]

            except Exception as err:
                print(err)
                sys.exit()
        return file_list

    def move_file(self, start_path: str, final_path: str) -> None:
        """
        Move the file from start_path to
        """

        # Create an instance of a Dropbox class, which can make requests to the API.
        with dropbox.Dropbox(
            oauth2_refresh_token=self.refresh_token, app_key=self.app_key
        ) as dbx:
            # Check that the access token is valid
            try:
                dbx.users_get_current_account()
            except AuthError:
                sys.exit("ERROR: Invalid access token.")
            try:
                dbx.files_move_v2(start_path, final_path)
            except ApiError as err:
                print(err)
                sys.exit()

    def delete_file(self, storage_path: str):
        """
        Remove the file from the dropbox
        """
        # Create an instance of a Dropbox class, which can make requests to the API.
        with dropbox.Dropbox(
            oauth2_refresh_token=self.refresh_token, app_key=self.app_key
        ) as dbx:
            # Check that the access token is valid
            try:
                dbx.users_get_current_account()
            except AuthError:
                sys.exit("ERROR: Invalid access token.")
            # We should really handle these exceptions cleaner, but this seems a bit
            # complicated right now
            # pylint: disable=W0703
            try:
                _ = dbx.files_delete(path=storage_path)
            except Exception as err:
                sys.exit(err)
