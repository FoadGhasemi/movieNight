from django.contrib.auth.models import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, username, password):
        """
        Creates and saves a User with the given username and password.
        """
        if not password:
            raise ValueError("Users must have an password address.")

        user = self.model(
            password = password,
            username = username,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password):
        """
        Creates and saves a superuser with the given username and password.
        """
        user = self.create_user(
            password=password,
            username=username,
        )
        user.is_admin = True
        user.save(using=self._db)
        return user

