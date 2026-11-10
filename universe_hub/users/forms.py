from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import StudentUser


class StudentUserCreationForm(UserCreationForm):
    university = forms.CharField(max_length=150, required=False, 
        label="Universidad", 
        help_text="Tu universidad (opcional)"
    )
    major = forms.CharField(max_length=150, required=False, 
        label="Carrera", 
        help_text="Tu carrera o ingeniería"
    )
    semester = forms.IntegerField(min_value=1, max_value=12, initial=1,
        label="Semestre",
        help_text="Semestre actual"
    )
    bio = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False,
        label="Biografía",
        help_text="Cuéntanos sobre ti y tus intereses académicos"
    )

    class Meta:
        model = StudentUser
        fields = ('username', 'email', 'university', 'major', 'semester', 'bio', 'password1', 'password2')
        labels = {
            'username': 'Nombre de usuario',
            'email': 'Correo electrónico',
            'password1': 'Contraseña',
            'password2': 'Confirmar contraseña',
        }


class StudentUserUpdateForm(forms.ModelForm):
    class Meta:
        model = StudentUser
        fields = ['first_name', 'last_name', 'university', 'major', 'semester', 'bio']
        labels = {
            'university': 'Universidad',
            'major': 'Carrera',
            'semester': 'Semestre actual',
            'bio': 'Biografía',
        }
        widgets = {
            # Cambiamos ClearableFileInput por FileInput para eliminar el "Borrar"
            'profile_picture': forms.FileInput(attrs={'class': 'custom-file-input'}),
            'cover_photo': forms.FileInput(attrs={'class': 'custom-file-input'}),
            'bio': forms.Textarea(attrs={'rows': 3, 'class': 'form-input'}),
        }