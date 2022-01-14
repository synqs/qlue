"""
Module that contains all the tests for this app folder.
"""

# pylint: disable=C0103

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse


class IndexPageTests(TestCase):
    """
    Test the title page
    """

    def test_call_index(self):
        """
        is it possible to reach the index page ?
        """
        url = reverse("index")
        r = self.client.get(url)
        self.assertEqual(r.status_code, 200)


class JobSubmissionTest(TestCase):
    """
    Test basic properties of the job submission process.
    """

    def setUp(self):
        self.username = "sandy"
        self.password = "dog"
        user = get_user_model().objects.create(username=self.username)
        user.set_password(self.password)
        user.save()
