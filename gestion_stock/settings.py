import os
import dj_database_url
from dotenv import load_dotenv
from pathlib import Path
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent

# Charger explicitement le fichier .env depuis la racine
load_dotenv(BASE_DIR / '.env')

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-tdsgu+xywwg0)txanecysk4trk_39d46(#ygybow(ind_%u_!m')

DEBUG = False

ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '.ngrok-free.dev',
    '.ngrok-free.app',
]

CSRF_TRUSTED_ORIGINS = [
    'https://*.ngrok-free.dev',
    'https://*.ngrok-free.app',
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',

    # Stockage Cloudinary (ordre strict requis)
    'cloudinary_storage',
    'django.contrib.staticfiles',
    'cloudinary',

    # Local apps
    'accounts',
    'stock',
    'fournisseurs',
    'clients',
    'achats',
    'ventes',
    'rapports',
    'parametres',
    'commandes',
    # API
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'api',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gestion_stock.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'accounts.context_processors.notifications',
                'accounts.context_processors.theme_utilisateur',
                'parametres.context_processors.config_magasin',
            ],
        },
    },
]

WSGI_APPLICATION = 'gestion_stock.wsgi.application'

# Configuration de la base de données Neon / PostgreSQL
DATABASE_URL = os.getenv('DATABASE_URL')

if not DATABASE_URL:
    raise ImproperlyConfigured(
        "DATABASE_URL n'est pas défini dans le fichier .env"
    )

DATABASES = {
    'default': dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=600,
        ssl_require=True
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Douala'
USE_I18N = True
USE_TZ = True

# Fichiers statiques et médias
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / "static",
]

# Configuration Cloudinary pour les médias
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
CLOUDINARY_STORAGE = {
    'CLOUDINARY_URL': os.getenv('CLOUDINARY_URL'),
}

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Authentification
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'rapports:tableau_de_bord'
LOGOUT_REDIRECT_URL = 'accounts:login'

WHATSAPP_INDICATIF_PAYS = '237'

# Conserver la session active pendant 14 jours (en secondes)
SESSION_COOKIE_AGE = 1209600

# Ne pas fermer la session à la fermeture du navigateur
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# =====================================================================
# API (Django REST Framework + JWT) pour le frontend React
# =====================================================================
from datetime import timedelta

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 30,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Origines autorisées à appeler l'API (le serveur de dev React de Vite par défaut).
# En production, on met l'adresse du frontend dans la variable CORS_ORIGINS.
CORS_ALLOWED_ORIGINS = [
    origine.strip()
    for origine in os.environ.get('CORS_ORIGINS', 'http://localhost:5173').split(',')
    if origine.strip()
]
