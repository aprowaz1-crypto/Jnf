from dataclasses import dataclass


@dataclass(frozen=True)
class CraftProfile:
    profile_id: str
    label: str
    category: str
    description: str
    thrust: int
    fuel_capacity: int
    stages: int
    drag_scale: float
    mass_scale: float
    radar: bool = False
    flight_program: bool = False
    max_g: int = 8
    gimbal_range: int = 4
    notes: str = ""


PROFILES = {
    "ballistic_missile": CraftProfile(
        profile_id="ballistic_missile",
        label="Ballistic Missile",
        category="Балістична ракета",
        description="Базовий профіль балістичної ракети без логіки перехоплення.",
        thrust=380000,
        fuel_capacity=9200,
        stages=1,
        drag_scale=0.24,
        mass_scale=0.9,
        max_g=4,
        gimbal_range=4,
        notes="Працює як звичайна ракета, а не як ПРО-перехоплювач.",
    ),
    "thaad": CraftProfile(
        profile_id="thaad",
        label="THAAD",
        category="Перехоплювач",
        description="Двоступеневий профіль ПРО з радаром і логікою прогнозного перехоплення.",
        thrust=420000,
        fuel_capacity=7600,
        stages=2,
        drag_scale=0.22,
        mass_scale=0.84,
        radar=True,
        flight_program=True,
        max_g=15,
        gimbal_range=12,
        notes="Для балістичних цілей та автономного наведення.",
    ),
    "patriot_pac3": CraftProfile(
        profile_id="patriot_pac3",
        label="Patriot PAC-3",
        category="Перехоплювач",
        description="Маневровий коротший профіль для швидкого пуску та точного доведення.",
        thrust=310000,
        fuel_capacity=4200,
        stages=1,
        drag_scale=0.18,
        mass_scale=0.78,
        radar=True,
        flight_program=True,
        max_g=18,
        gimbal_range=14,
        notes="Коротка ракета з високою керованістю.",
    ),
    "interceptor_10mach": CraftProfile(
        profile_id="interceptor_10mach",
        label="10 Mach Interceptor",
        category="Перехоплювач",
        description="Швидкісний шаблон для перехоплення гіперзвукових цілей.",
        thrust=450000,
        fuel_capacity=6800,
        stages=2,
        drag_scale=0.2,
        mass_scale=0.8,
        radar=True,
        flight_program=True,
        max_g=20,
        gimbal_range=15,
        notes="Підвищена тяга та керування для цілей до 10 Махів.",
    ),
    "orbital_launcher": CraftProfile(
        profile_id="orbital_launcher",
        label="Orbital Launcher",
        category="Ракета-носій",
        description="Універсальний пусковий профіль для виведення корисного навантаження на орбіту.",
        thrust=520000,
        fuel_capacity=18000,
        stages=2,
        drag_scale=0.28,
        mass_scale=1.05,
        max_g=6,
        gimbal_range=5,
        notes="Збалансований профіль для старту та орбітального доведення.",
    ),
    "sounding_rocket": CraftProfile(
        profile_id="sounding_rocket",
        label="Sounding Rocket",
        category="Дослідницький крафт",
        description="Легка ракета для суборбітальних місій, тестів та швидких експериментів.",
        thrust=170000,
        fuel_capacity=2200,
        stages=1,
        drag_scale=0.16,
        mass_scale=0.7,
        max_g=5,
        gimbal_range=3,
        notes="Простий профіль для навчальних запусків.",
    ),
    "orbital_tug": CraftProfile(
        profile_id="orbital_tug",
        label="Orbital Tug",
        category="Орбітальний апарат",
        description="Крафт для маневрів на орбіті, стикування та переміщення корисного навантаження.",
        thrust=90000,
        fuel_capacity=5400,
        stages=1,
        drag_scale=0.45,
        mass_scale=0.92,
        max_g=3,
        gimbal_range=2,
        notes="Оптимізований для вакууму і повторних маневрів.",
    ),
}
