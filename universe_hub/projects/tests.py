from django.test import TestCase, Client
from django.urls import reverse
from users.models import StudentUser
from posts.models import Project, ProjectApplication


class ProjectsAndApplicationsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.owner = StudentUser.objects.create_user(
            username='lider_proyecto',
            email='lider@udg.mx',
            password='Password123!',
            university='CUALTOS',
            major='Ingeniería en Computación',
            semester=6,
        )
        self.applicant = StudentUser.objects.create_user(
            username='postulante',
            email='postulante@udg.mx',
            password='Password123!',
            university='CUALTOS',
            major='Diseño',
            semester=4,
        )
        self.project = Project.objects.create(
            owner=self.owner,
            title='Sistema de Tutorías',
            summary='Plataforma para conectar tutores y alumnos',
            description='Descripción completa del proyecto de tutorías',
            problem_and_goal='Mejorar el rendimiento académico en la universidad',
            project_type='class',
            stage='idea',
            vacancies=1,
            target_careers='engineering, design',
            required_skills='Python, Figma',
            work_mode='remote',
            status='open',
        )

    def test_project_detail_view(self):
        self.client.login(username='postulante', password='Password123!')
        response = self.client.get(reverse('project_detail', kwargs={'project_id': self.project.id}))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['project'], self.project)
        self.assertFalse(response.context['is_owner'])

    def test_apply_to_project(self):
        self.client.login(username='postulante', password='Password123!')
        url = reverse('apply_to_project', kwargs={'project_id': self.project.id})
        response = self.client.post(url)
        self.assertRedirects(response, reverse('project_detail', kwargs={'project_id': self.project.id}))

        application = ProjectApplication.objects.filter(project=self.project, applicant=self.applicant).first()
        self.assertIsNotNone(application)
        self.assertEqual(application.status, 'pending')

    def test_cannot_apply_to_own_project(self):
        self.client.login(username='lider_proyecto', password='Password123!')
        url = reverse('apply_to_project', kwargs={'project_id': self.project.id})
        response = self.client.post(url)
        self.assertRedirects(response, reverse('project_detail', kwargs={'project_id': self.project.id}))
        self.assertFalse(ProjectApplication.objects.filter(project=self.project, applicant=self.owner).exists())

    def test_accept_application_and_close_project(self):
        # Crear postulación previa
        app = ProjectApplication.objects.create(
            project=self.project,
            applicant=self.applicant,
            status='pending'
        )

        self.client.login(username='lider_proyecto', password='Password123!')
        url = reverse('accept_application', kwargs={'application_id': app.id})
        response = self.client.post(url)
        self.assertRedirects(response, reverse('home'))

        app.refresh_from_db()
        self.assertEqual(app.status, 'accepted')

        self.project.refresh_from_db()
        self.assertEqual(self.project.vacancies, 0)
        self.assertEqual(self.project.status, 'closed')

    def test_reject_application(self):
        app = ProjectApplication.objects.create(
            project=self.project,
            applicant=self.applicant,
            status='pending'
        )

        self.client.login(username='lider_proyecto', password='Password123!')
        url = reverse('reject_application', kwargs={'application_id': app.id})
        response = self.client.post(url)
        self.assertRedirects(response, reverse('home'))

        app.refresh_from_db()
        self.assertEqual(app.status, 'rejected')
