from django.contrib.auth.base_user import AbstractBaseUser
from django.db import models
from .managers import UserManager


class User(AbstractBaseUser):
    # Add niche fields here later
    is_premium = models.BooleanField(default=False)
    username = models.CharField(max_length=20)
    bio = models.TextField(max_length=500, blank=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)
    password = models.CharField(max_length=4, unique=True)
    email = models.EmailField()

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False, verbose_name="ادمین")
    objects = UserManager()

    USERNAME_FIELD = "password"
    REQUIRED_FIELDS = ["fullname"]

    def __str__(self):
        return self.username


    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin
