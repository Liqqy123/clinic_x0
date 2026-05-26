import random
from datetime import date, time, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils.module_loading import import_string

from faker import Faker

from appointments.models import Appointment
from main.models import Doctor, Patient, Specialization
from users.models import CustomUser


class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми данными через Faker'

    def add_arguments(self, parser):
        parser.add_argument(
            '--doctors',
            type=int,
            default=10,
            help='Количество врачей, которые будут созданы',
        )
        parser.add_argument(
            '--patients',
            type=int,
            default=20,
            help='Количество пациентов, которые будут созданы',
        )
        parser.add_argument(
            '--appointments',
            type=int,
            default=40,
            help='Количество записей на приём, которые будут созданы',
        )
        parser.add_argument(
            '--specializations',
            type=int,
            default=8,
            help='Количество специализаций, которые будут созданы',
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Очистить тестовые данные перед заполнением',
        )
        parser.add_argument(
            '--locale',
            type=str,
            default=None,
            help='Локаль Faker, переопределяет settings.FAKER_LOCALE',
        )
        parser.add_argument(
            '--providers',
            nargs='+',
            default=None,
            help='Дополнительные провайдеры Faker, например faker.providers.address',
        )

    def handle(self, *args, **options):
        locale = options['locale'] or getattr(settings, 'FAKER_LOCALE', None) or 'ru_RU'
        providers = options['providers'] or getattr(settings, 'FAKER_PROVIDERS', None) or []
        if isinstance(providers, str):
            providers = [providers]
        faker = Faker(locale)

        for provider_path in providers:
            self.add_provider(faker, provider_path)

        self.stdout.write(f'Faker locale: {locale}')
        if providers:
            self.stdout.write(f'Faker providers: {providers}')

        if options['clear']:
            self.clear_data()

        specializations = self.create_specializations(options['specializations'], faker)
        doctors = self.create_doctors(options['doctors'], specializations, faker)
        patients = self.create_patients(options['patients'], faker)
        self.create_appointments(options['appointments'], doctors, patients, faker)

        self.stdout.write(self.style.SUCCESS('Заполнение базы данных завершено.'))

    def add_provider(self, faker, provider_path):
        try:
            provider_cls = import_string(provider_path)
        except Exception as exc:
            raise CommandError(f'Не удалось импортировать провайдера Faker: {provider_path} ({exc})')
        faker.add_provider(provider_cls)
        self.stdout.write(f'Добавлен провайдер Faker: {provider_path}')

    def clear_data(self):
        Appointment.objects.all().delete()
        Doctor.objects.all().delete()
        Patient.objects.all().delete()
        Specialization.objects.all().delete()
        CustomUser.objects.filter(role__in=['doctor', 'patient']).delete()
        self.stdout.write(self.style.WARNING('Тестовые данные удалены.'))

    def create_specializations(self, count, faker):
        names = [
            'Терапевт',
            'Кардиолог',
            'Невролог',
            'Хирург',
            'Педиатр',
            'Офтальмолог',
            'Стоматолог',
            'Дерматолог',
            'Уролог',
            'Эндокринолог',
            'ЛОР',
        ]
        if count > len(names):
            extra = [faker.job() for _ in range(count - len(names))]
            names.extend(extra)
        names = names[:count]
        
        names = list(dict.fromkeys(names))
        
        while len(names) < count:
            new_name = faker.job()
            if new_name not in names:
                names.append(new_name)

        specializations = []
        for name in names:
            try:
                specialization, created = Specialization.objects.get_or_create(
                    name=name,
                    defaults={'description': faker.text(max_nb_chars=100)},
                )
                specializations.append(specialization)
                self.stdout.write(f'✓ Специализация: {specialization.name}')
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f'⚠ Специализация "{name}" не создана: {exc}'))
                continue

        return specializations

    def create_doctors(self, count, specializations, faker):
        doctors = []
        attempts = 0
        max_attempts = count * 3
        
        while len(doctors) < count and attempts < max_attempts:
            attempts += 1
            try:
                first_name = faker.first_name()
                last_name = faker.last_name()
                username = self.unique_username(first_name, last_name)
                email = faker.ascii_email()
                phone = self.unique_phone(faker)
                
                user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    password='password123',
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    role='doctor',
                )
                specialization = random.choice(specializations)
                doctor = Doctor.objects.create(
                    user=user,
                    name=f'{first_name} {last_name}',
                    specialization=specialization,
                    experience=random.randint(3, 30),
                    bio=faker.text(max_nb_chars=150),
                    phone=phone,
                    email=email,
                    degree=random.choice(['Кандидат наук', 'Доктор наук', 'Врач высшей категории', 'Первая категория', 'Вторая категория']),
                    clinic_address=faker.address(),
                    specialization_list='\n'.join(faker.words(nb=4)),
                )
                doctors.append(doctor)
                self.stdout.write(f'✓ Врач: {doctor.name} ({specialization.name})')
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f'⚠ Врач не создан: {exc}'))
                continue

        return doctors

    def create_patients(self, count, faker):
        patients = []
        attempts = 0
        max_attempts = count * 3
        
        while len(patients) < count and attempts < max_attempts:
            attempts += 1
            try:
                first_name = faker.first_name()
                last_name = faker.last_name()
                username = self.unique_username(first_name, last_name)
                email = faker.ascii_email()
                phone = self.unique_phone(faker)
                
                user = CustomUser.objects.create_user(
                    username=username,
                    email=email,
                    password='password123',
                    first_name=first_name,
                    last_name=last_name,
                    phone=phone,
                    role='patient',
                )
                patient = Patient.objects.create(
                    user=user,
                    patient_id=f'P{faker.unique.random_number(digits=6, fix_len=True)}',
                    first_name=first_name,
                    last_name=last_name,
                    age=random.randint(1, 90),
                    gender=random.choice(['M', 'F']),
                    phone=phone,
                    email=email,
                    address=faker.address(),
                    allergies=random.choice(['', 'Нет', 'Пыльца', 'Молоко', 'Морепродукты']),
                    medical_history=faker.text(max_nb_chars=120),
                )
                patients.append(patient)
                self.stdout.write(f'✓ Пациент: {patient.patient_id} - {patient.first_name} {patient.last_name}')
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f'⚠ Пациент не создан: {exc}'))
                continue

        return patients

    def create_appointments(self, count, doctors, patients, faker):
        if not doctors or not patients:
            return

        statuses = [choice[0] for choice in Appointment.STATUS_CHOICES]
        created_count = 0
        
        for _ in range(count * 2):
            if created_count >= count:
                break
            try:
                patient = random.choice(patients)
                doctor = random.choice(doctors)
                appointment_date = date.today() + timedelta(days=random.randint(1, 45))
                appointment_time = time.fromisoformat(faker.time(pattern='%H:%M'))
                status = random.choice(statuses)
                Appointment.objects.create(
                    user=patient.user,
                    doctor=doctor,
                    date=appointment_date,
                    time=appointment_time,
                    notes=faker.text(max_nb_chars=120),
                    status=status,
                )
                created_count += 1
            except Exception as exc:
                self.stdout.write(self.style.WARNING(f'⚠ Запись на приём не создана: {exc}'))
                continue
        
        self.stdout.write(f'✓ Записи на приём: {created_count}')

    def unique_username(self, first_name, last_name):
        base = f'{first_name.lower()}.{last_name.lower()}'
        username = base
        counter = 1
        while CustomUser.objects.filter(username=username).exists():
            username = f'{base}{counter}'
            counter += 1
        return username

    def unique_phone(self, faker):
        attempts = 0
        while attempts < 100:
            phone = f'+7{faker.numerify("9#########")}'
            if not CustomUser.objects.filter(phone=phone).exists():
                return phone
            attempts += 1
        raise ValueError("Не удалось создать уникальный номер телефона")
