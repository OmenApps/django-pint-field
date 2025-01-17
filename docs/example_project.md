
# Example Project

## Overview

The example project demonstrates the functionality of `django-pint-field`. The project contains two main apps: `example` and `laboratory`, which showcase different aspects of the package.

## Apps

### Example App

The `example` app provides basic demonstrations of the field types and their usage with:
- **Model Examples**: Using `IntegerPintField`, ~~`BigIntegerPintField`~~, and `DecimalPintField` to store and retrieve Pint quantities in the database.
- **REST Framework Integration**: Integration with Django REST Framework (DRF) and Django Ninja to demonstrate how to serialize and deserialize Pint quantities in APIs.
- **Admin Interface Customization**: Customizing the Django admin interface to display Pint quantities.
- **Form Handling**: Handling Pint quantities in Django forms.
- **Cache Integration**: Integration with `django-cachalot` and `django-cacheops` for caching specific models and for testing serialization.

This app is primarily used for automated testing.

### F.L.M.N. Laboratory App

The Fictional Laboratory Monitoring Network (F.L.M.N.), aka `laboratory` app provides a full-featured fictional laboratory tracking management system that showcases real*ish*-world usage of `django-pint-field` in a complex application. It includes:
- **Interactive Dashboards**: Real-time monitoring of laboratory metrics, dimensional stability tracking, and incident mapping.
- **Laboratory and Universe Management**: Managing laboratories, universes, equipment, substances, and more.
- **Management Commands**: Commands for data population and feature demonstration.

## Getting Started

### Prerequisites
- Docker and Docker Compose [installed](https://docs.docker.com/compose/install/) on your system
- Git (to clone the `django-pint-field` repository)

### Setting Up the Project

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/OmenApps/django-pint-field.git
   cd django-pint-field
   ```

2. **Build and Start the Containers**:
   ```bash
   docker compose up -d --build
   ```

   This will start three containers:
   - Django development server (accessible at http://localhost:8115)
   - PostgreSQL database
   - Redis server (for caching)

3. **Create a Superuser**:
If you want to view the admin, you will need to create a superuser account.
   ```bash
   docker compose exec django python manage.py createsuperuser
   ```

4. **Access the Application**:
   - Main application: http://localhost:8115
   - Admin interface: http://localhost:8115/admin

### Management Commands

The laboratory app includes two management commands:

1. **Populate the Database**:
Adds lots and lots of example data.
   ```bash
   docker compose exec django python manage.py populate
   ```

2. **Demonstrate Features**:
Displays a cheatsheet in the console to view examples of how to manipulate and display pint field values in the console or code.
   ```bash
   docker compose exec django python manage.py cheatsheet
   ```

   Access the cheatsheet through the UI at: http://localhost:8115/cheatsheet/

### Running Tests

To run the test suite:
```bash
docker compose exec django pytest
```

For coverage report:
```bash
docker compose exec django coverage run -m pytest
docker compose exec django coverage report
```

## Key Features to Explore

1. **Measurement Systems**
   - Handling various units of measurement
   - Custom unit definitions in [`settings.py`](https://github.com/OmenApps/django-pint-field/blob/main/example_project/settings.py)
   - Unit conversion capabilities

2. **API Integration**
   - REST framework serializers with `django-pint-field`
   - Django Ninja integration

3. **Dashboard Features**
   - Real-time monitoring of metrics for laboratories in 12 different fictional universes
   - Multiple dashboards with various ways to display pint fields ([pic](https://raw.githubusercontent.com/OmenApps/django-pint-field/refs/heads/main/docs/media/localhost_8115_dashboard.png), [pic](https://raw.githubusercontent.com/OmenApps/django-pint-field/refs/heads/main/docs/media/localhost_8115_dashboard_incidents_.png), [pic](https://raw.githubusercontent.com/OmenApps/django-pint-field/refs/heads/main/docs/media/localhost_8115_dashboard_stability_.png), [pic](https://raw.githubusercontent.com/OmenApps/django-pint-field/refs/heads/main/docs/media/localhost_8115_dashboard_status_.png))

4. **Laboratory Management**
   - Universe and laboratory administration
   - Tracking and reporting on
      - Laboratory status ([pic](https://raw.githubusercontent.com/OmenApps/django-pint-field/refs/heads/main/docs/media/localhost_8115_laboratories_.png))
      - Experimental Devices at each laboratory ([pic](https://raw.githubusercontent.com/OmenApps/django-pint-field/refs/heads/main/docs/media/localhost_8115_devices_1_.png))
      - Anomalous Substances stored at the labs ([pic](https://raw.githubusercontent.com/OmenApps/django-pint-field/refs/heads/main/docs/media/localhost_8115_substances_2_.png), [pic](https://raw.githubusercontent.com/OmenApps/django-pint-field/refs/heads/main/docs/media/localhost_8115_substances_74_.png))
      - Test Subjects present at each lab ([pic](https://raw.githubusercontent.com/OmenApps/django-pint-field/refs/heads/main/docs/media/localhost_8115_subjects_48_.png))
      - Incidents that have occurred at each lab ([pic](https://raw.githubusercontent.com/OmenApps/django-pint-field/refs/heads/main/docs/media/localhost_8115_incidents_2_.png))
      - Dimensional Rifts caused by or affecting each lab ([pic](https://raw.githubusercontent.com/OmenApps/django-pint-field/refs/heads/main/docs/media/localhost_8115_rifts_3_.png))
      - Safety Protocol that F.L.M.N. personnel may need to apply based on incidents that occur ([pic](https://raw.githubusercontent.com/OmenApps/django-pint-field/refs/heads/main/docs/media/localhost_8115_protocols_270_.png))
      - Energy Readings at each lab ([pic](https://raw.githubusercontent.com/OmenApps/django-pint-field/refs/heads/main/docs/media/localhost_8115_energy_344_.png))

5. **Cache Integration to Validate Serialization/Pickling**
   - `django-cachalot`
   - `django-cacheops`
   - Redis-based caching configuration

## Additional Information

- **Admin Interface**: The Django admin interface provides a way to manage the data in the `example` and `laboratory` apps. You can view and edit models like `IntegerPintFieldSaveModel`, `ExperimentalDevice`, and `AnomalousSubstance`.

- **Templates**: The `laboratory` app includes various templates that demonstrate how to display Pint quantities in a user-friendly way. These templates use custom filters and tags provided by `django-pint-field`.

- **APIs**: The `example` app provides API endpoints using both Django REST Framework and Django Ninja.

- **Caching**: The project is configured to use Redis for caching, with `django-cachalot` and `cacheops` for testing of database query caching.

- **Custom Units**: The project defines several custom units in the `settings.py` file, which can be used in the models and templates.

- **Testing**: The project includes a comprehensive test suite that covers the functionality of `django-pint-field` in various scenarios.
