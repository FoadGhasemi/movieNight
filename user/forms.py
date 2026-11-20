from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError

User = get_user_model()


class UserCreationForm(forms.ModelForm):
    """A form for creating new users. Includes all the required
    fields, plus a repeated password."""

    username = forms.CharField(label="نام کاربری", widget=forms.TextInput(attrs={"class": "form-control"}))
    password1 = forms.CharField(label="گذر واژه", widget=forms.PasswordInput(attrs={"placeholder": "گذرواژه",
                                                                                    "class": "form-control"}))
    password2 = forms.CharField(label="تایید گذر واژه", widget=forms.PasswordInput(attrs={"placeholder": "تکرار گذرواژه",
                                                                                          "class": "form-control"}))

    class Meta:
        model = User
        fields = ["username", "password1", "password2"]
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "نام کامل"}),
        }

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError("پسورد %(value)s از پسورد اول متفاوت است",
                                  code='non_matching_passwords',
                                  params={'value': f'{password2}'})
        return password2

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    """A form for updating users. Includes all the fields on
    the user, but replaces the password field with admin's
    disabled password hash display field.
    """

    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ["email", "password", "username", "bio", "avatar", "is_active", "is_admin"]


class UserUpdateForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ["email", "password", "username", "bio", "avatar", "is_active", "is_admin"]
        widgets = {
            "fullname": forms.TextInput(attrs={"placeholder": "نام کامل"}),
        }

    def save(self, commit=True):
        # Save the provided password in hashed format
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserLoginForm(forms.Form):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control"})
    )