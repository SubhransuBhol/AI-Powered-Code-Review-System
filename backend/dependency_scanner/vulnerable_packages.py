# Static database of package rules
# Maps package names (lowercase) to their threshold versions
# vulnerable_below: if package version < vulnerable_below -> Security Risk (HIGH)
# outdated_below: if vulnerable_below <= package version < outdated_below -> Maintenance Risk (LOW)

PYTHON_RULES = {
    "requests": {
        "vulnerable_below": (2, 29, 0),
        "outdated_below": (2, 32, 0),
    },
    "flask": {
        "vulnerable_below": (2, 0, 0),
        "outdated_below": (3, 0, 0),
    },
    "django": {
        "vulnerable_below": (4, 2, 11),
        "outdated_below": (5, 0, 0),
    },
    "jinja2": {
        "vulnerable_below": (3, 1, 3),
        "outdated_below": (3, 1, 4),
    },
    "urllib3": {
        "vulnerable_below": (1, 26, 17),
        "outdated_below": (2, 2, 0),
    },
    "cryptography": {
        "vulnerable_below": (42, 0, 4),
        "outdated_below": (42, 0, 5),
    }
}

NPM_RULES = {
    "express": {
        "vulnerable_below": (4, 19, 2),
        "outdated_below": (4, 20, 0),
    },
    "lodash": {
        "vulnerable_below": (4, 17, 21),
        "outdated_below": (4, 17, 22),
    },
    "axios": {
        "vulnerable_below": (1, 6, 0),
        "outdated_below": (1, 7, 0),
    },
    "jsonwebtoken": {
        "vulnerable_below": (9, 0, 0),
        "outdated_below": (9, 0, 2),
    },
    "semver": {
        "vulnerable_below": (7, 5, 2),
        "outdated_below": (7, 6, 0),
    }
}
