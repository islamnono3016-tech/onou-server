"""
وحدة بذر وترحيل بيانات الإقامة الجامعية حساني محمد بن إبراهيم (RES-04 / residence_id=4)
لشهري سبتمبر وأكتوبر 2026 بدقة تامة ومطابقة 100% لسجلات الإكسل الرسمية.
"""

import logging
import sqlite3

logger = logging.getLogger("SeedResidence4")

INITIAL_STOCKS = {
  "35": 1891.0,
  "36": 283.0,
  "39": 67.0,
  "43": 1060.0,
  "44": 177.0,
  "45": 300.0,
  "46": 370.0,
  "47": 60937.0,
  "48": 315.0,
  "49": 118023.0,
  "37": 135.0,
  "50": 11168.0,
  "52": 7626.0,
  "38": 989.0,
  "58": 255.0,
  "59": 5156.0,
  "67": 41854.0,
  "68": 26.0,
  "69": 655.0,
  "71": 329.0,
  "72": 163.0
}

DAILY_DATA = [
  {
    "date": "2026-09-01",
    "supply": [],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [],
    "bf_students": 0,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 0,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 0,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 0.0,
    "lu_expense": 0.0,
    "di_expense": 0.0,
    "total_expense": 0.0
  },
  {
    "date": "2026-09-02",
    "supply": [],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [],
    "bf_students": 0,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 0,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 0,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 0.0,
    "lu_expense": 0.0,
    "di_expense": 0.0,
    "total_expense": 0.0
  },
  {
    "date": "2026-09-03",
    "supply": [],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [],
    "bf_students": 0,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 0,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 0,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 0.0,
    "lu_expense": 0.0,
    "di_expense": 0.0,
    "total_expense": 0.0
  },
  {
    "date": "2026-09-04",
    "supply": [],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [],
    "bf_students": 0,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 0,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 0,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 0.0,
    "lu_expense": 0.0,
    "di_expense": 0.0,
    "total_expense": 0.0
  },
  {
    "date": "2026-09-05",
    "supply": [],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [],
    "bf_students": 0,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 0,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 0,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 0.0,
    "lu_expense": 0.0,
    "di_expense": 0.0,
    "total_expense": 0.0
  },
  {
    "date": "2026-09-06",
    "supply": [],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [],
    "bf_students": 0,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 0,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 0,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 0.0,
    "lu_expense": 0.0,
    "di_expense": 0.0,
    "total_expense": 0.0
  },
  {
    "date": "2026-09-07",
    "supply": [],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [],
    "bf_students": 0,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 0,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 0,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 0.0,
    "lu_expense": 0.0,
    "di_expense": 0.0,
    "total_expense": 0.0
  },
  {
    "date": "2026-09-08",
    "supply": [],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [],
    "bf_students": 0,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 0,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 0,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 0.0,
    "lu_expense": 0.0,
    "di_expense": 0.0,
    "total_expense": 0.0
  },
  {
    "date": "2026-09-09",
    "supply": [],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [],
    "bf_students": 0,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 0,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 0,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 0.0,
    "lu_expense": 0.0,
    "di_expense": 0.0,
    "total_expense": 0.0
  },
  {
    "date": "2026-09-10",
    "supply": [],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [],
    "bf_students": 0,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 0,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 0,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 0.0,
    "lu_expense": 0.0,
    "di_expense": 0.0,
    "total_expense": 0.0
  },
  {
    "date": "2026-09-11",
    "supply": [],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [],
    "bf_students": 0,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 0,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 0,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 0.0,
    "lu_expense": 0.0,
    "di_expense": 0.0,
    "total_expense": 0.0
  },
  {
    "date": "2026-09-12",
    "supply": [],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [],
    "bf_students": 0,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 0,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 0,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 0.0,
    "lu_expense": 0.0,
    "di_expense": 0.0,
    "total_expense": 0.0
  },
  {
    "date": "2026-09-13",
    "supply": [],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [],
    "bf_students": 0,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 0,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 0,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 0.0,
    "lu_expense": 0.0,
    "di_expense": 0.0,
    "total_expense": 0.0
  },
  {
    "date": "2026-09-14",
    "supply": [],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [],
    "bf_students": 0,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 0,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 0,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 0.0,
    "lu_expense": 0.0,
    "di_expense": 0.0,
    "total_expense": 0.0
  },
  {
    "date": "2026-09-15",
    "supply": [],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [],
    "bf_students": 0,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 0,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 0,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 0.0,
    "lu_expense": 0.0,
    "di_expense": 0.0,
    "total_expense": 0.0
  },
  {
    "date": "2026-09-16",
    "supply": [
      {
        "article_id": 4,
        "quantity": 6000.0,
        "unit_price_ttc": 16.0
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [],
    "bf_students": 0,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 0,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 0,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 0.0,
    "lu_expense": 0.0,
    "di_expense": 0.0,
    "total_expense": 0.0
  },
  {
    "date": "2026-09-17",
    "supply": [],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [],
    "bf_students": 0,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 0,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 0,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 0.0,
    "lu_expense": 0.0,
    "di_expense": 0.0,
    "total_expense": 0.0
  },
  {
    "date": "2026-09-18",
    "supply": [],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [],
    "bf_students": 0,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 0,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 0,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 0.0,
    "lu_expense": 0.0,
    "di_expense": 0.0,
    "total_expense": 0.0
  },
  {
    "date": "2026-09-19",
    "supply": [
      {
        "article_id": 5,
        "quantity": 202.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 7,
        "quantity": 39.0,
        "unit_price_ttc": 130.0
      },
      {
        "article_id": 9,
        "quantity": 171.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "quantity": 741.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "quantity": 627.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 15,
        "quantity": 295.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 17,
        "quantity": 29.0,
        "unit_price_ttc": 150.0
      },
      {
        "article_id": 21,
        "quantity": 303.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "quantity": 203.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 30,
        "quantity": 8.0,
        "unit_price_ttc": 400.0
      },
      {
        "article_id": 33,
        "quantity": 260.0,
        "unit_price_ttc": 65.0
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [],
    "bf_students": 0,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 0,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 0,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 0.0,
    "lu_expense": 0.0,
    "di_expense": 0.0,
    "total_expense": 0.0
  },
  {
    "date": "2026-09-20",
    "supply": [],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [],
    "bf_students": 0,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 0,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 0,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 0.0,
    "lu_expense": 0.0,
    "di_expense": 0.0,
    "total_expense": 0.0
  },
  {
    "date": "2026-09-21",
    "supply": [
      {
        "article_id": 77,
        "quantity": 100.0,
        "unit_price_ttc": 571.1999999999999
      },
      {
        "article_id": 80,
        "quantity": 2400.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 82,
        "quantity": 4800.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 83,
        "quantity": 800.0,
        "unit_price_ttc": 218.95999999999998
      }
    ],
    "loan_in": [
      {
        "article_id": 57,
        "quantity": 24.0,
        "unit_price_ttc": 357.0
      }
    ],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 15.0,
        "total_qty": 15.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 7,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 5.0,
        "total_qty": 5.0,
        "unit_price_ttc": 130.0
      },
      {
        "article_id": 9,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 5.0,
        "total_qty": 5.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 20.0,
        "total_qty": 20.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 35.0,
        "total_qty": 35.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 15,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 18.0,
        "total_qty": 18.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 30,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 2.0,
        "total_qty": 2.0,
        "unit_price_ttc": 400.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 15.0,
        "total_qty": 15.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1.0,
        "total_qty": 1.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 48,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 40.0,
        "total_qty": 40.0,
        "unit_price_ttc": 207.10000000000002
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 312.0,
        "total_qty": 312.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 6.0,
        "total_qty": 6.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 2.0,
        "total_qty": 2.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 4.0,
        "total_qty": 4.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 3.0,
        "total_qty": 3.0,
        "unit_price_ttc": 595.0
      }
    ],
    "bf_students": 0,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 0,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 55,
    "di_staff": 71,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 0.0,
    "lu_expense": 0.0,
    "di_expense": 73961.2,
    "total_expense": 73961.2
  },
  {
    "date": "2026-09-22",
    "supply": [
      {
        "article_id": 82,
        "quantity": 720.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 91,
        "quantity": 200.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "quantity": 600.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [
      {
        "article_id": 42,
        "quantity": 50.0,
        "unit_price_ttc": 152.60000000000002
      }
    ],
    "loan_out": [
      {
        "article_id": 44,
        "total_qty": 50.0,
        "unit_price_ttc": 272.5
      }
    ],
    "kitchen": [
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 400.0,
        "qty_dinner": 120.0,
        "total_qty": 520.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 7,
        "qty_breakfast": 0.0,
        "qty_lunch": 8.0,
        "qty_dinner": 8.0,
        "total_qty": 16.0,
        "unit_price_ttc": 130.0
      },
      {
        "article_id": 9,
        "qty_breakfast": 0.0,
        "qty_lunch": 16.0,
        "qty_dinner": 10.0,
        "total_qty": 26.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 18.0,
        "qty_dinner": 17.0,
        "total_qty": 35.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 15,
        "qty_breakfast": 0.0,
        "qty_lunch": 20.0,
        "qty_dinner": 18.0,
        "total_qty": 38.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 17,
        "qty_breakfast": 0.0,
        "qty_lunch": 4.0,
        "qty_dinner": 5.0,
        "total_qty": 9.0,
        "unit_price_ttc": 150.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 15.0,
        "qty_dinner": 15.0,
        "total_qty": 30.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "qty_breakfast": 0.0,
        "qty_lunch": 18.0,
        "qty_dinner": 15.0,
        "total_qty": 33.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 30,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 2.0,
        "total_qty": 2.0,
        "unit_price_ttc": 400.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 15.0,
        "qty_dinner": 15.0,
        "total_qty": 30.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 3.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 3.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 3.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 3.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 42,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 30.0,
        "total_qty": 30.0,
        "unit_price_ttc": 152.60000000000002
      },
      {
        "article_id": 44,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 0.0,
        "total_qty": 30.0,
        "unit_price_ttc": 272.5
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 5.0,
        "total_qty": 5.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 37,
        "qty_breakfast": 2.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 2.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 52,
        "qty_breakfast": 0.0,
        "qty_lunch": 148.0,
        "qty_dinner": 165.0,
        "total_qty": 313.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 38,
        "qty_breakfast": 2.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 2.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 5.0,
        "qty_dinner": 6.0,
        "total_qty": 11.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 3.0,
        "qty_dinner": 3.0,
        "total_qty": 6.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 3.0,
        "qty_dinner": 4.0,
        "total_qty": 7.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 3.0,
        "qty_dinner": 3.0,
        "total_qty": 6.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 3.0,
        "total_qty": 5.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 80,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 170.0,
        "total_qty": 170.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 82,
        "qty_breakfast": 0.0,
        "qty_lunch": 155.0,
        "qty_dinner": 0.0,
        "total_qty": 155.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 83,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 35.0,
        "total_qty": 35.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 91,
        "qty_breakfast": 200.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 200.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "qty_breakfast": 100.0,
        "qty_lunch": 250.0,
        "qty_dinner": 250.0,
        "total_qty": 600.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 11,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 80,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 97,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 16672.199999999997,
    "lu_expense": 39107.4825,
    "di_expense": 42263.65,
    "total_expense": 98043.33249999999
  },
  {
    "date": "2026-09-23",
    "supply": [
      {
        "article_id": 3,
        "quantity": 260.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 35,
        "quantity": 360.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 37,
        "quantity": 100.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 57,
        "quantity": 500.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "quantity": 200.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 60,
        "quantity": 165.0,
        "unit_price_ttc": 487.9
      },
      {
        "article_id": 61,
        "quantity": 600.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 73,
        "quantity": 500.0,
        "unit_price_ttc": 1142.3999999999999
      },
      {
        "article_id": 95,
        "quantity": 500.0,
        "unit_price_ttc": 40.81
      },
      {
        "article_id": 98,
        "quantity": 1300.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [
      {
        "article_id": 57,
        "quantity": 12.0,
        "unit_price_ttc": 357.0
      }
    ],
    "loan_out": [
      {
        "article_id": 46,
        "total_qty": 20.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 67,
        "total_qty": 600.0,
        "unit_price_ttc": 26.18
      }
    ],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 20.0,
        "qty_dinner": 200.0,
        "total_qty": 220.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 90.0,
        "qty_dinner": 120.0,
        "total_qty": 210.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 7,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 12.0,
        "total_qty": 12.0,
        "unit_price_ttc": 130.0
      },
      {
        "article_id": 9,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 45.0,
        "total_qty": 75.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 22.0,
        "qty_dinner": 58.0,
        "total_qty": 80.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 15,
        "qty_breakfast": 0.0,
        "qty_lunch": 28.0,
        "qty_dinner": 42.0,
        "total_qty": 70.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 17,
        "qty_breakfast": 0.0,
        "qty_lunch": 5.0,
        "qty_dinner": 5.0,
        "total_qty": 10.0,
        "unit_price_ttc": 150.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 28.0,
        "qty_dinner": 52.0,
        "total_qty": 80.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "qty_breakfast": 0.0,
        "qty_lunch": 35.0,
        "qty_dinner": 48.0,
        "total_qty": 83.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 30,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 400.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 25.0,
        "qty_dinner": 28.0,
        "total_qty": 53.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 10.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 10.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 8.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 8.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 3.0,
        "total_qty": 4.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 42,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 10.0,
        "total_qty": 20.0,
        "unit_price_ttc": 152.60000000000002
      },
      {
        "article_id": 46,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 70.0,
        "total_qty": 70.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 47,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 0.0,
        "total_qty": 50.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 10.0,
        "total_qty": 10.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 37,
        "qty_breakfast": 4.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 736.0,
        "qty_dinner": 0.0,
        "total_qty": 736.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 52,
        "qty_breakfast": 0.0,
        "qty_lunch": 365.0,
        "qty_dinner": 698.0,
        "total_qty": 1063.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 38,
        "qty_breakfast": 3.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 3.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 5.0,
        "qty_dinner": 12.0,
        "total_qty": 17.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 4.0,
        "qty_dinner": 5.0,
        "total_qty": 9.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 60,
        "qty_breakfast": 0.0,
        "qty_lunch": 5.0,
        "qty_dinner": 5.0,
        "total_qty": 10.0,
        "unit_price_ttc": 487.9
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 368.0,
        "qty_dinner": 0.0,
        "total_qty": 368.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 3.0,
        "qty_dinner": 3.0,
        "total_qty": 6.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 4.0,
        "qty_dinner": 5.0,
        "total_qty": 9.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 3.0,
        "total_qty": 5.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 73,
        "qty_breakfast": 0.0,
        "qty_lunch": 5.0,
        "qty_dinner": 5.0,
        "total_qty": 10.0,
        "unit_price_ttc": 1142.3999999999999
      },
      {
        "article_id": 82,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 715.0,
        "total_qty": 715.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 95,
        "qty_breakfast": 500.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 500.0,
        "unit_price_ttc": 40.81
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 400.0,
        "qty_dinner": 700.0,
        "total_qty": 1300.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 222,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 311,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 645,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 42898.6,
    "lu_expense": 157753.88999999998,
    "di_expense": 188958.82249999998,
    "total_expense": 389611.3125
  },
  {
    "date": "2026-09-24",
    "supply": [
      {
        "article_id": 96,
        "quantity": 600.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "quantity": 1750.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [
      {
        "article_id": 65,
        "quantity": 30.0,
        "unit_price_ttc": 1142.3999999999999
      }
    ],
    "loan_out": [
      {
        "article_id": 67,
        "total_qty": 1200.0,
        "unit_price_ttc": 26.18
      }
    ],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 20.0,
        "qty_dinner": 20.0,
        "total_qty": 40.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 150.0,
        "qty_dinner": 150.0,
        "total_qty": 300.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 42.0,
        "qty_dinner": 45.0,
        "total_qty": 87.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 9,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 35.0,
        "total_qty": 65.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 45.0,
        "qty_dinner": 0.0,
        "total_qty": 45.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "qty_breakfast": 0.0,
        "qty_lunch": 140.0,
        "qty_dinner": 0.0,
        "total_qty": 140.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 15,
        "qty_breakfast": 0.0,
        "qty_lunch": 28.0,
        "qty_dinner": 32.0,
        "total_qty": 60.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 17,
        "qty_breakfast": 0.0,
        "qty_lunch": 3.0,
        "qty_dinner": 4.0,
        "total_qty": 7.0,
        "unit_price_ttc": 150.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 40.0,
        "qty_dinner": 45.0,
        "total_qty": 85.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "qty_breakfast": 0.0,
        "qty_lunch": 42.0,
        "qty_dinner": 0.0,
        "total_qty": 42.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 38.0,
        "qty_dinner": 40.0,
        "total_qty": 78.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 10.0,
        "qty_lunch": 0.0,
        "qty_dinner": 4.0,
        "total_qty": 14.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 12.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 12.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 43,
        "qty_breakfast": 0.0,
        "qty_lunch": 60.0,
        "qty_dinner": 0.0,
        "total_qty": 60.0,
        "unit_price_ttc": 348.8
      },
      {
        "article_id": 37,
        "qty_breakfast": 3.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 3.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1436.0,
        "total_qty": 1436.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 52,
        "qty_breakfast": 0.0,
        "qty_lunch": 672.0,
        "qty_dinner": 708.0,
        "total_qty": 1380.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 38,
        "qty_breakfast": 3.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 3.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 12.0,
        "qty_dinner": 8.0,
        "total_qty": 20.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 3.0,
        "qty_dinner": 4.0,
        "total_qty": 7.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 59,
        "qty_breakfast": 0.0,
        "qty_lunch": 670.0,
        "qty_dinner": 0.0,
        "total_qty": 670.0,
        "unit_price_ttc": 190.39999999999998
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 65,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 30.0,
        "total_qty": 30.0,
        "unit_price_ttc": 1142.3999999999999
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 675.0,
        "qty_dinner": 0.0,
        "total_qty": 675.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 2.0,
        "total_qty": 3.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 4.0,
        "qty_dinner": 4.0,
        "total_qty": 8.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 73,
        "qty_breakfast": 0.0,
        "qty_lunch": 5.0,
        "qty_dinner": 5.0,
        "total_qty": 10.0,
        "unit_price_ttc": 1142.3999999999999
      },
      {
        "article_id": 77,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 40.0,
        "total_qty": 50.0,
        "unit_price_ttc": 571.1999999999999
      },
      {
        "article_id": 80,
        "qty_breakfast": 270.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 270.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 82,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 715.0,
        "total_qty": 715.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 96,
        "qty_breakfast": 600.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 600.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "qty_breakfast": 150.0,
        "qty_lunch": 800.0,
        "qty_dinner": 800.0,
        "total_qty": 1750.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 252,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 637,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 688,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 50404.4,
    "lu_expense": 300286.0,
    "di_expense": 309833.2225,
    "total_expense": 660523.6225
  },
  {
    "date": "2026-09-25",
    "supply": [
      {
        "article_id": 91,
        "quantity": 600.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "quantity": 1650.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 150.0,
        "qty_dinner": 150.0,
        "total_qty": 300.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 45.0,
        "qty_dinner": 42.0,
        "total_qty": 87.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 42.0,
        "qty_dinner": 32.0,
        "total_qty": 74.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 180.0,
        "total_qty": 180.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 15,
        "qty_breakfast": 0.0,
        "qty_lunch": 48.0,
        "qty_dinner": 45.0,
        "total_qty": 93.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 17,
        "qty_breakfast": 0.0,
        "qty_lunch": 3.0,
        "qty_dinner": 0.0,
        "total_qty": 3.0,
        "unit_price_ttc": 150.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 42.0,
        "qty_dinner": 40.0,
        "total_qty": 82.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 28.0,
        "qty_dinner": 26.0,
        "total_qty": 54.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 12.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 12.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 10.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 10.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 46,
        "qty_breakfast": 0.0,
        "qty_lunch": 70.0,
        "qty_dinner": 0.0,
        "total_qty": 70.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 47,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 60.0,
        "total_qty": 60.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 37,
        "qty_breakfast": 3.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 3.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 1398.0,
        "qty_dinner": 0.0,
        "total_qty": 1398.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 52,
        "qty_breakfast": 0.0,
        "qty_lunch": 705.0,
        "qty_dinner": 0.0,
        "total_qty": 705.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 38,
        "qty_breakfast": 3.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 3.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 12.0,
        "qty_dinner": 13.0,
        "total_qty": 25.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 4.0,
        "qty_dinner": 4.0,
        "total_qty": 8.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 59,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 705.0,
        "total_qty": 705.0,
        "unit_price_ttc": 190.39999999999998
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 720.0,
        "qty_dinner": 0.0,
        "total_qty": 720.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 3.0,
        "qty_dinner": 3.0,
        "total_qty": 6.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 80,
        "qty_breakfast": 282.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 282.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 83,
        "qty_breakfast": 35.0,
        "qty_lunch": 15.0,
        "qty_dinner": 0.0,
        "total_qty": 50.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 91,
        "qty_breakfast": 600.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 600.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "qty_breakfast": 150.0,
        "qty_lunch": 800.0,
        "qty_dinner": 700.0,
        "total_qty": 1650.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 278,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 696,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 701,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 63872.2,
    "lu_expense": 245501.15,
    "di_expense": 252222.89999999997,
    "total_expense": 561596.25
  },
  {
    "date": "2026-09-26",
    "supply": [
      {
        "article_id": 5,
        "quantity": 181.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 7,
        "quantity": 40.0,
        "unit_price_ttc": 130.0
      },
      {
        "article_id": 9,
        "quantity": 171.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "quantity": 117.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "quantity": 402.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 14,
        "quantity": 226.0,
        "unit_price_ttc": 200.0
      },
      {
        "article_id": 15,
        "quantity": 46.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 21,
        "quantity": 255.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "quantity": 113.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 33,
        "quantity": 183.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 95,
        "quantity": 500.0,
        "unit_price_ttc": 40.81
      },
      {
        "article_id": 98,
        "quantity": 1750.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 1386.0,
        "qty_dinner": 120.0,
        "total_qty": 1506.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 20.0,
        "qty_dinner": 18.0,
        "total_qty": 38.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 9,
        "qty_breakfast": 0.0,
        "qty_lunch": 25.0,
        "qty_dinner": 20.0,
        "total_qty": 45.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 28.0,
        "qty_dinner": 70.0,
        "total_qty": 98.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 220.0,
        "total_qty": 220.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 14,
        "qty_breakfast": 0.0,
        "qty_lunch": 150.0,
        "qty_dinner": 0.0,
        "total_qty": 150.0,
        "unit_price_ttc": 200.0
      },
      {
        "article_id": 15,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 10.0,
        "total_qty": 20.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 32.0,
        "qty_dinner": 28.0,
        "total_qty": 60.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "qty_breakfast": 0.0,
        "qty_lunch": 28.0,
        "qty_dinner": 35.0,
        "total_qty": 63.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 35.0,
        "qty_dinner": 20.0,
        "total_qty": 55.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 12.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 12.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 10.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 10.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 2.0,
        "total_qty": 3.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 47,
        "qty_breakfast": 0.0,
        "qty_lunch": 60.0,
        "qty_dinner": 0.0,
        "total_qty": 60.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 37,
        "qty_breakfast": 4.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1790.0,
        "total_qty": 1790.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 52,
        "qty_breakfast": 0.0,
        "qty_lunch": 645.0,
        "qty_dinner": 895.0,
        "total_qty": 1540.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 38,
        "qty_breakfast": 4.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 14.0,
        "qty_dinner": 10.0,
        "total_qty": 24.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 4.0,
        "qty_dinner": 4.0,
        "total_qty": 8.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 4.0,
        "qty_dinner": 4.0,
        "total_qty": 8.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 73,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 15.0,
        "total_qty": 25.0,
        "unit_price_ttc": 1142.3999999999999
      },
      {
        "article_id": 77,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 20.0,
        "total_qty": 30.0,
        "unit_price_ttc": 571.1999999999999
      },
      {
        "article_id": 80,
        "qty_breakfast": 245.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 245.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 95,
        "qty_breakfast": 500.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 500.0,
        "unit_price_ttc": 40.81
      },
      {
        "article_id": 98,
        "qty_breakfast": 150.0,
        "qty_lunch": 700.0,
        "qty_dinner": 900.0,
        "total_qty": 1750.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 238,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 633,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 887,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 51008.3,
    "lu_expense": 119368.15,
    "di_expense": 387256.65,
    "total_expense": 557633.1000000001
  },
  {
    "date": "2026-09-27",
    "supply": [
      {
        "article_id": 3,
        "quantity": 300.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 91,
        "quantity": 800.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "quantity": 2100.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 25.0,
        "qty_dinner": 275.0,
        "total_qty": 300.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 28.0,
        "qty_dinner": 20.0,
        "total_qty": 48.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 9,
        "qty_breakfast": 0.0,
        "qty_lunch": 32.0,
        "qty_dinner": 0.0,
        "total_qty": 32.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 15.0,
        "qty_dinner": 40.0,
        "total_qty": 55.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 250.0,
        "total_qty": 250.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 15,
        "qty_breakfast": 0.0,
        "qty_lunch": 20.0,
        "qty_dinner": 22.0,
        "total_qty": 42.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 38.0,
        "qty_dinner": 0.0,
        "total_qty": 38.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 0.0,
        "total_qty": 30.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 25.0,
        "qty_dinner": 25.0,
        "total_qty": 50.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 14.0,
        "qty_lunch": 0.0,
        "qty_dinner": 4.0,
        "total_qty": 18.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 12.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 12.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 4.0,
        "total_qty": 5.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 47,
        "qty_breakfast": 0.0,
        "qty_lunch": 70.0,
        "qty_dinner": 0.0,
        "total_qty": 70.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 37,
        "qty_breakfast": 4.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 1872.0,
        "qty_dinner": 0.0,
        "total_qty": 1872.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 52,
        "qty_breakfast": 0.0,
        "qty_lunch": 885.0,
        "qty_dinner": 1075.0,
        "total_qty": 1960.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 38,
        "qty_breakfast": 4.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 14.0,
        "qty_dinner": 5.0,
        "total_qty": 19.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 5.0,
        "qty_dinner": 4.0,
        "total_qty": 9.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 60,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 0.0,
        "total_qty": 10.0,
        "unit_price_ttc": 487.9
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 882.0,
        "qty_dinner": 0.0,
        "total_qty": 882.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 4.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 0.0,
        "total_qty": 2.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 73,
        "qty_breakfast": 0.0,
        "qty_lunch": 15.0,
        "qty_dinner": 220.0,
        "total_qty": 235.0,
        "unit_price_ttc": 1142.3999999999999
      },
      {
        "article_id": 77,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 20.0,
        "total_qty": 20.0,
        "unit_price_ttc": 571.1999999999999
      },
      {
        "article_id": 82,
        "qty_breakfast": 380.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 380.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 91,
        "qty_breakfast": 800.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 800.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 900.0,
        "qty_dinner": 1000.0,
        "total_qty": 2100.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 373,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 876,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1065,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 72199.97,
    "lu_expense": 337985.51,
    "di_expense": 539263.65,
    "total_expense": 949449.13
  },
  {
    "date": "2026-09-28",
    "supply": [
      {
        "article_id": 52,
        "quantity": 6048.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 91,
        "quantity": 700.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "quantity": 2500.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 210.0,
        "qty_dinner": 0.0,
        "total_qty": 210.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 20.0,
        "qty_dinner": 18.0,
        "total_qty": 38.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 7,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 10.0,
        "total_qty": 10.0,
        "unit_price_ttc": 130.0
      },
      {
        "article_id": 9,
        "qty_breakfast": 0.0,
        "qty_lunch": 9.0,
        "qty_dinner": 0.0,
        "total_qty": 9.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 58.0,
        "qty_dinner": 28.0,
        "total_qty": 86.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "qty_breakfast": 0.0,
        "qty_lunch": 154.0,
        "qty_dinner": 0.0,
        "total_qty": 154.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 14,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 76.0,
        "total_qty": 76.0,
        "unit_price_ttc": 200.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 27.0,
        "qty_dinner": 0.0,
        "total_qty": 27.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 18.0,
        "qty_dinner": 15.0,
        "total_qty": 33.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 14.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 14.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 12.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 12.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 44,
        "qty_breakfast": 0.0,
        "qty_lunch": 97.0,
        "qty_dinner": 0.0,
        "total_qty": 97.0,
        "unit_price_ttc": 272.5
      },
      {
        "article_id": 45,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 10.0,
        "total_qty": 10.0,
        "unit_price_ttc": 403.3
      },
      {
        "article_id": 47,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 90.0,
        "total_qty": 90.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 10.0,
        "total_qty": 10.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 2324.0,
        "total_qty": 2324.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 52,
        "qty_breakfast": 0.0,
        "qty_lunch": 1045.0,
        "qty_dinner": 1170.0,
        "total_qty": 2215.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 38,
        "qty_breakfast": 4.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 16.0,
        "qty_dinner": 18.0,
        "total_qty": 34.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 7.0,
        "total_qty": 13.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 59,
        "qty_breakfast": 0.0,
        "qty_lunch": 1040.0,
        "qty_dinner": 0.0,
        "total_qty": 1040.0,
        "unit_price_ttc": 190.39999999999998
      },
      {
        "article_id": 60,
        "qty_breakfast": 0.0,
        "qty_lunch": 5.0,
        "qty_dinner": 0.0,
        "total_qty": 5.0,
        "unit_price_ttc": 487.9
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 1168.0,
        "qty_dinner": 0.0,
        "total_qty": 1168.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 6.0,
        "total_qty": 12.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 4.0,
        "total_qty": 5.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 73,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 5.0,
        "total_qty": 15.0,
        "unit_price_ttc": 1142.3999999999999
      },
      {
        "article_id": 80,
        "qty_breakfast": 345.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 345.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 83,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 0.0,
        "total_qty": 10.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 91,
        "qty_breakfast": 700.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 700.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 1100.0,
        "qty_dinner": 1200.0,
        "total_qty": 2500.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 33,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 1034,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1162,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 64021.1,
    "lu_expense": 388032.18999999994,
    "di_expense": 365076.2,
    "total_expense": 817129.49
  },
  {
    "date": "2026-09-29",
    "supply": [
      {
        "article_id": 3,
        "quantity": 500.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 34,
        "quantity": 100.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 36,
        "quantity": 300.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "quantity": 150.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 43,
        "quantity": 600.0,
        "unit_price_ttc": 348.8
      },
      {
        "article_id": 44,
        "quantity": 350.0,
        "unit_price_ttc": 272.5
      },
      {
        "article_id": 45,
        "quantity": 500.0,
        "unit_price_ttc": 403.3
      },
      {
        "article_id": 46,
        "quantity": 500.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 47,
        "quantity": 450.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 48,
        "quantity": 400.0,
        "unit_price_ttc": 207.10000000000002
      },
      {
        "article_id": 50,
        "quantity": 13800.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 51,
        "quantity": 100.0,
        "unit_price_ttc": 1737.3999999999999
      },
      {
        "article_id": 53,
        "quantity": 50.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 62,
        "quantity": 150.0,
        "unit_price_ttc": 1904.0
      },
      {
        "article_id": 63,
        "quantity": 150.0,
        "unit_price_ttc": 1190.0
      },
      {
        "article_id": 67,
        "quantity": 20007.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "quantity": 100.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "quantity": 250.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 95,
        "quantity": 800.0,
        "unit_price_ttc": 40.81
      },
      {
        "article_id": 98,
        "quantity": 2400.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 20.0,
        "qty_dinner": 275.0,
        "total_qty": 295.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 210.0,
        "qty_dinner": 518.0,
        "total_qty": 728.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 12.0,
        "qty_dinner": 12.0,
        "total_qty": 24.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 7,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 10.0,
        "total_qty": 20.0,
        "unit_price_ttc": 130.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 25.0,
        "qty_dinner": 35.0,
        "total_qty": 60.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 20.0,
        "qty_dinner": 0.0,
        "total_qty": 20.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 12.0,
        "total_qty": 22.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 3.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 3.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 14.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 14.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 12.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 12.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 45,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 10.0,
        "total_qty": 20.0,
        "unit_price_ttc": 403.3
      },
      {
        "article_id": 47,
        "qty_breakfast": 0.0,
        "qty_lunch": 90.0,
        "qty_dinner": 0.0,
        "total_qty": 90.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 48,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 90.0,
        "total_qty": 90.0,
        "unit_price_ttc": 207.10000000000002
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 10.0,
        "total_qty": 20.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 37,
        "qty_breakfast": 4.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 2100.0,
        "qty_dinner": 0.0,
        "total_qty": 2100.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 52,
        "qty_breakfast": 0.0,
        "qty_lunch": 1035.0,
        "qty_dinner": 1045.0,
        "total_qty": 2080.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 16.0,
        "qty_dinner": 16.0,
        "total_qty": 32.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 6.0,
        "total_qty": 12.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 1038.0,
        "qty_dinner": 1050.0,
        "total_qty": 2088.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 0.0,
        "total_qty": 2.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 6.0,
        "total_qty": 12.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 73,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 5.0,
        "total_qty": 15.0,
        "unit_price_ttc": 1142.3999999999999
      },
      {
        "article_id": 83,
        "qty_breakfast": 0.0,
        "qty_lunch": 40.0,
        "qty_dinner": 0.0,
        "total_qty": 40.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 95,
        "qty_breakfast": 800.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 800.0,
        "unit_price_ttc": 40.81
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 1100.0,
        "qty_dinner": 1100.0,
        "total_qty": 2400.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 375,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 1028,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1037,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 65581.2,
    "lu_expense": 375345.59,
    "di_expense": 236516.85,
    "total_expense": 677443.64
  },
  {
    "date": "2026-09-30",
    "supply": [
      {
        "article_id": 48,
        "quantity": 300.0,
        "unit_price_ttc": 207.10000000000002
      },
      {
        "article_id": 49,
        "quantity": 200.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 79,
        "quantity": 2400.0,
        "unit_price_ttc": 29.75
      },
      {
        "article_id": 80,
        "quantity": 2400.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 83,
        "quantity": 50.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 92,
        "quantity": 894.0,
        "unit_price_ttc": 8.5
      },
      {
        "article_id": 98,
        "quantity": 2400.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 205.0,
        "qty_dinner": 0.0,
        "total_qty": 205.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 150.0,
        "qty_dinner": 150.0,
        "total_qty": 300.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 7,
        "qty_breakfast": 0.0,
        "qty_lunch": 5.0,
        "qty_dinner": 5.0,
        "total_qty": 10.0,
        "unit_price_ttc": 130.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 55.0,
        "qty_dinner": 85.0,
        "total_qty": 140.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 20.0,
        "qty_dinner": 0.0,
        "total_qty": 20.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 5.0,
        "qty_dinner": 5.0,
        "total_qty": 10.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 4.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 14.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 14.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 12.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 12.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 43,
        "qty_breakfast": 0.0,
        "qty_lunch": 90.0,
        "qty_dinner": 0.0,
        "total_qty": 90.0,
        "unit_price_ttc": 348.8
      },
      {
        "article_id": 45,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 10.0,
        "total_qty": 10.0,
        "unit_price_ttc": 403.3
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 10.0,
        "total_qty": 10.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 120.0,
        "qty_dinner": 2518.0,
        "total_qty": 2638.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 51,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 30.0,
        "total_qty": 30.0,
        "unit_price_ttc": 1737.3999999999999
      },
      {
        "article_id": 52,
        "qty_breakfast": 0.0,
        "qty_lunch": 945.0,
        "qty_dinner": 1145.0,
        "total_qty": 2090.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 0.0,
        "total_qty": 2.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 38,
        "qty_breakfast": 4.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 18.0,
        "qty_dinner": 18.0,
        "total_qty": 36.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 6.0,
        "total_qty": 12.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 62,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 30.0,
        "total_qty": 30.0,
        "unit_price_ttc": 1904.0
      },
      {
        "article_id": 63,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 30.0,
        "total_qty": 30.0,
        "unit_price_ttc": 1190.0
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 940.0,
        "qty_dinner": 1145.0,
        "total_qty": 2085.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 6.0,
        "total_qty": 12.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 4.0,
        "qty_dinner": 3.0,
        "total_qty": 7.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 73,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 190.0,
        "total_qty": 190.0,
        "unit_price_ttc": 1142.3999999999999
      },
      {
        "article_id": 79,
        "qty_breakfast": 435.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 435.0,
        "unit_price_ttc": 29.75
      },
      {
        "article_id": 83,
        "qty_breakfast": 0.0,
        "qty_lunch": 35.0,
        "qty_dinner": 40.0,
        "total_qty": 75.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 92,
        "qty_breakfast": 894.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 894.0,
        "unit_price_ttc": 8.5
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 1000.0,
        "qty_dinner": 1200.0,
        "total_qty": 2400.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 428,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 925,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1139,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 43615.05,
    "lu_expense": 218300.65000000002,
    "di_expense": 758406.35,
    "total_expense": 1020322.05
  },
  {
    "date": "2026-10-01",
    "supply": [
      {
        "article_id": 3,
        "quantity": 600.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "quantity": 12000.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 96,
        "quantity": 800.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "quantity": 2500.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 300.0,
        "total_qty": 330.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 300.0,
        "qty_dinner": 0.0,
        "total_qty": 300.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 9,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 0.0,
        "total_qty": 10.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 65.0,
        "qty_dinner": 15.0,
        "total_qty": 80.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 0.0,
        "total_qty": 30.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 4.0,
        "qty_dinner": 4.0,
        "total_qty": 8.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 4.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 14.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 14.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 13.0,
        "qty_lunch": 0.0,
        "qty_dinner": 18.0,
        "total_qty": 31.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 4.0,
        "total_qty": 6.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 43,
        "qty_breakfast": 0.0,
        "qty_lunch": 100.0,
        "qty_dinner": 0.0,
        "total_qty": 100.0,
        "unit_price_ttc": 348.8
      },
      {
        "article_id": 48,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 110.0,
        "total_qty": 110.0,
        "unit_price_ttc": 207.10000000000002
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 15.0,
        "total_qty": 15.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 180.0,
        "qty_dinner": 0.0,
        "total_qty": 180.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 51,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 35.0,
        "total_qty": 35.0,
        "unit_price_ttc": 1737.3999999999999
      },
      {
        "article_id": 52,
        "qty_breakfast": 0.0,
        "qty_lunch": 328.0,
        "qty_dinner": 0.0,
        "total_qty": 328.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 38,
        "qty_breakfast": 4.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 18.0,
        "qty_dinner": 20.0,
        "total_qty": 38.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 6.0,
        "total_qty": 12.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 59,
        "qty_breakfast": 0.0,
        "qty_lunch": 1080.0,
        "qty_dinner": 0.0,
        "total_qty": 1080.0,
        "unit_price_ttc": 190.39999999999998
      },
      {
        "article_id": 62,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 30.0,
        "total_qty": 30.0,
        "unit_price_ttc": 1904.0
      },
      {
        "article_id": 63,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 30.0,
        "total_qty": 30.0,
        "unit_price_ttc": 1190.0
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 1082.0,
        "qty_dinner": 0.0,
        "total_qty": 1082.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 3.0,
        "total_qty": 3.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 6.0,
        "total_qty": 12.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 71,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 3.0,
        "total_qty": 3.0,
        "unit_price_ttc": 130.9
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 3.0,
        "total_qty": 3.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 79,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1225.0,
        "total_qty": 1225.0,
        "unit_price_ttc": 29.75
      },
      {
        "article_id": 82,
        "qty_breakfast": 369.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 369.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 96,
        "qty_breakfast": 800.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 800.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 1100.0,
        "qty_dinner": 1200.0,
        "total_qty": 2500.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 360,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 1077,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1216,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 68760.4235,
    "lu_expense": 343380.16,
    "di_expense": 382032.05,
    "total_expense": 794172.6335
  },
  {
    "date": "2026-10-02",
    "supply": [
      {
        "article_id": 91,
        "quantity": 800.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "quantity": 2500.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 270.0,
        "qty_dinner": 0.0,
        "total_qty": 270.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 600.0,
        "qty_dinner": 0.0,
        "total_qty": 600.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 15.0,
        "total_qty": 45.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 4.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 14.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 14.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 12.0,
        "qty_lunch": 0.0,
        "qty_dinner": 16.0,
        "total_qty": 28.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 4.0,
        "qty_dinner": 2.0,
        "total_qty": 6.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 46,
        "qty_breakfast": 0.0,
        "qty_lunch": 100.0,
        "qty_dinner": 0.0,
        "total_qty": 100.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 47,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 100.0,
        "total_qty": 100.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 15.0,
        "qty_dinner": 15.0,
        "total_qty": 30.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 2338.0,
        "total_qty": 2338.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 51,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 35.0,
        "total_qty": 35.0,
        "unit_price_ttc": 1737.3999999999999
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 38,
        "qty_breakfast": 4.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 22.0,
        "qty_dinner": 20.0,
        "total_qty": 42.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 6.0,
        "total_qty": 12.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 62,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 30.0,
        "total_qty": 30.0,
        "unit_price_ttc": 1904.0
      },
      {
        "article_id": 63,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 30.0,
        "total_qty": 30.0,
        "unit_price_ttc": 1190.0
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1175.0,
        "total_qty": 1175.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 71,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 3.0,
        "total_qty": 3.0,
        "unit_price_ttc": 130.9
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 79,
        "qty_breakfast": 365.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 365.0,
        "unit_price_ttc": 29.75
      },
      {
        "article_id": 82,
        "qty_breakfast": 0.0,
        "qty_lunch": 1115.0,
        "qty_dinner": 0.0,
        "total_qty": 1115.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 91,
        "qty_breakfast": 800.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 800.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 1100.0,
        "qty_dinner": 1200.0,
        "total_qty": 2500.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 361,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 1109,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1169,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 75916.75,
    "lu_expense": 200638.7225,
    "di_expense": 506683.8,
    "total_expense": 783239.2725
  },
  {
    "date": "2026-10-03",
    "supply": [
      {
        "article_id": 5,
        "quantity": 489.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 9,
        "quantity": 236.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "quantity": 806.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "quantity": 903.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 15,
        "quantity": 349.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 21,
        "quantity": 399.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "quantity": 469.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 30,
        "quantity": 2.0,
        "unit_price_ttc": 400.0
      },
      {
        "article_id": 33,
        "quantity": 440.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 95,
        "quantity": 900.0,
        "unit_price_ttc": 40.81
      },
      {
        "article_id": 98,
        "quantity": 2800.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 210.0,
        "qty_dinner": 150.0,
        "total_qty": 360.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 48.0,
        "qty_dinner": 52.0,
        "total_qty": 100.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 9,
        "qty_breakfast": 0.0,
        "qty_lunch": 40.0,
        "qty_dinner": 38.0,
        "total_qty": 78.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 55.0,
        "qty_dinner": 45.0,
        "total_qty": 100.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "qty_breakfast": 0.0,
        "qty_lunch": 250.0,
        "qty_dinner": 0.0,
        "total_qty": 250.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 15,
        "qty_breakfast": 0.0,
        "qty_lunch": 38.0,
        "qty_dinner": 40.0,
        "total_qty": 78.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 42.0,
        "qty_dinner": 40.0,
        "total_qty": 82.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "qty_breakfast": 0.0,
        "qty_lunch": 42.0,
        "qty_dinner": 42.0,
        "total_qty": 84.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 30,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 400.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 35.0,
        "qty_dinner": 32.0,
        "total_qty": 67.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 4.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 14.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 14.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 12.0,
        "qty_lunch": 0.0,
        "qty_dinner": 16.0,
        "total_qty": 28.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 3.0,
        "total_qty": 5.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 44,
        "qty_breakfast": 0.0,
        "qty_lunch": 100.0,
        "qty_dinner": 0.0,
        "total_qty": 100.0,
        "unit_price_ttc": 272.5
      },
      {
        "article_id": 48,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 120.0,
        "total_qty": 120.0,
        "unit_price_ttc": 207.10000000000002
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 2510.0,
        "qty_dinner": 3294.0,
        "total_qty": 5804.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 2.0,
        "total_qty": 3.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 38,
        "qty_breakfast": 4.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 16.0,
        "qty_dinner": 24.0,
        "total_qty": 40.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 5.0,
        "total_qty": 11.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 62,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 30.0,
        "total_qty": 30.0,
        "unit_price_ttc": 1904.0
      },
      {
        "article_id": 63,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 30.0,
        "total_qty": 30.0,
        "unit_price_ttc": 1190.0
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1516.0,
        "total_qty": 1516.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 6.0,
        "total_qty": 12.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 83,
        "qty_breakfast": 55.0,
        "qty_lunch": 15.0,
        "qty_dinner": 15.0,
        "total_qty": 85.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 95,
        "qty_breakfast": 900.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 900.0,
        "unit_price_ttc": 40.81
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 1100.0,
        "qty_dinner": 1500.0,
        "total_qty": 2800.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 411,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 1135,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1507,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 82348.7,
    "lu_expense": 488219.0,
    "di_expense": 611649.28,
    "total_expense": 1182216.98
  },
  {
    "date": "2026-10-04",
    "supply": [
      {
        "article_id": 3,
        "quantity": 650.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 86,
        "quantity": 341.0,
        "unit_price_ttc": 952.0
      },
      {
        "article_id": 89,
        "quantity": 1400.0,
        "unit_price_ttc": 46.648
      },
      {
        "article_id": 91,
        "quantity": 1000.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "quantity": 2600.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 20.0,
        "qty_dinner": 360.0,
        "total_qty": 380.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 210.0,
        "qty_dinner": 180.0,
        "total_qty": 390.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 42.0,
        "qty_dinner": 40.0,
        "total_qty": 82.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 9,
        "qty_breakfast": 0.0,
        "qty_lunch": 41.0,
        "qty_dinner": 42.0,
        "total_qty": 83.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 38.0,
        "qty_dinner": 220.0,
        "total_qty": 258.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "qty_breakfast": 0.0,
        "qty_lunch": 180.0,
        "qty_dinner": 0.0,
        "total_qty": 180.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 15,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 32.0,
        "total_qty": 62.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 48.0,
        "qty_dinner": 45.0,
        "total_qty": 93.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "qty_breakfast": 0.0,
        "qty_lunch": 48.0,
        "qty_dinner": 45.0,
        "total_qty": 93.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 36.0,
        "qty_dinner": 35.0,
        "total_qty": 71.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 5.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 5.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 14.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 14.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 12.0,
        "qty_lunch": 0.0,
        "qty_dinner": 18.0,
        "total_qty": 30.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 5.0,
        "total_qty": 15.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 47,
        "qty_breakfast": 0.0,
        "qty_lunch": 100.0,
        "qty_dinner": 0.0,
        "total_qty": 100.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 20.0,
        "total_qty": 20.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 38,
        "qty_breakfast": 5.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 5.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 16.0,
        "qty_dinner": 18.0,
        "total_qty": 34.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 6.0,
        "total_qty": 12.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 62,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 30.0,
        "total_qty": 30.0,
        "unit_price_ttc": 1904.0
      },
      {
        "article_id": 63,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 30.0,
        "total_qty": 30.0,
        "unit_price_ttc": 1190.0
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 1015.0,
        "qty_dinner": 1405.0,
        "total_qty": 2420.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 6.0,
        "total_qty": 12.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 71,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 4.0,
        "total_qty": 4.0,
        "unit_price_ttc": 130.9
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 83,
        "qty_breakfast": 55.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 55.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 86,
        "qty_breakfast": 0.0,
        "qty_lunch": 341.0,
        "qty_dinner": 0.0,
        "total_qty": 341.0,
        "unit_price_ttc": 952.0
      },
      {
        "article_id": 89,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1400.0,
        "total_qty": 1400.0,
        "unit_price_ttc": 46.648
      },
      {
        "article_id": 91,
        "qty_breakfast": 1000.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 1000.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 1000.0,
        "qty_dinner": 1400.0,
        "total_qty": 2600.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 423,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 999,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1387,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 88870.3,
    "lu_expense": 503763.30000000005,
    "di_expense": 433313.3,
    "total_expense": 1025946.9000000001
  },
  {
    "date": "2026-10-05",
    "supply": [
      {
        "article_id": 96,
        "quantity": 1000.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "quantity": 3000.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 270.0,
        "qty_dinner": 0.0,
        "total_qty": 270.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 180.0,
        "qty_dinner": 180.0,
        "total_qty": 360.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 42.0,
        "qty_dinner": 40.0,
        "total_qty": 82.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 9,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 35.0,
        "total_qty": 65.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 45.0,
        "qty_dinner": 35.0,
        "total_qty": 80.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 15,
        "qty_breakfast": 0.0,
        "qty_lunch": 35.0,
        "qty_dinner": 38.0,
        "total_qty": 73.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 38.0,
        "qty_dinner": 40.0,
        "total_qty": 78.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 38.0,
        "qty_dinner": 32.0,
        "total_qty": 70.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 5.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 5.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 14.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 14.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 12.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 12.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 4.0,
        "qty_dinner": 2.0,
        "total_qty": 6.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 44,
        "qty_breakfast": 0.0,
        "qty_lunch": 110.0,
        "qty_dinner": 0.0,
        "total_qty": 110.0,
        "unit_price_ttc": 272.5
      },
      {
        "article_id": 48,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 130.0,
        "total_qty": 130.0,
        "unit_price_ttc": 207.10000000000002
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 15.0,
        "total_qty": 15.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 38,
        "qty_breakfast": 5.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 5.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 18.0,
        "qty_dinner": 24.0,
        "total_qty": 42.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 7.0,
        "total_qty": 13.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 59,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1562.0,
        "total_qty": 1562.0,
        "unit_price_ttc": 190.39999999999998
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 1168.0,
        "qty_dinner": 1560.0,
        "total_qty": 2728.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 3.0,
        "total_qty": 5.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 7.0,
        "total_qty": 13.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 2.0,
        "total_qty": 3.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 83,
        "qty_breakfast": 60.0,
        "qty_lunch": 15.0,
        "qty_dinner": 0.0,
        "total_qty": 75.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 96,
        "qty_breakfast": 1000.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 1000.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 1200.0,
        "qty_dinner": 1600.0,
        "total_qty": 3000.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 460,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 1154,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1555,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 84134.1,
    "lu_expense": 231931.24,
    "di_expense": 422408.8,
    "total_expense": 738474.1399999999
  },
  {
    "date": "2026-10-06",
    "supply": [
      {
        "article_id": 3,
        "quantity": 670.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 52,
        "quantity": 8064.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 86,
        "quantity": 311.0,
        "unit_price_ttc": 952.0
      },
      {
        "article_id": 91,
        "quantity": 1000.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "quantity": 2700.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [
      {
        "article_id": 15,
        "total_qty": 15.0,
        "unit_price_ttc": 110.0
      }
    ],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 20.0,
        "qty_dinner": 350.0,
        "total_qty": 370.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 150.0,
        "qty_dinner": 0.0,
        "total_qty": 150.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 9,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 0.0,
        "total_qty": 10.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 25.0,
        "qty_dinner": 90.0,
        "total_qty": 115.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 15,
        "qty_breakfast": 0.0,
        "qty_lunch": 24.0,
        "qty_dinner": 16.0,
        "total_qty": 40.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 46.0,
        "qty_dinner": 0.0,
        "total_qty": 46.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "qty_breakfast": 0.0,
        "qty_lunch": 52.0,
        "qty_dinner": 0.0,
        "total_qty": 52.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 28.0,
        "qty_dinner": 48.0,
        "total_qty": 76.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 5.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 5.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 14.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 14.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 13.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 13.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 12.0,
        "qty_dinner": 6.0,
        "total_qty": 18.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 47,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 110.0,
        "total_qty": 110.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 15.0,
        "total_qty": 15.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 52,
        "qty_breakfast": 0.0,
        "qty_lunch": 1215.0,
        "qty_dinner": 1295.0,
        "total_qty": 2510.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 38,
        "qty_breakfast": 5.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 5.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 14.0,
        "qty_dinner": 24.0,
        "total_qty": 38.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 7.0,
        "qty_dinner": 6.0,
        "total_qty": 13.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 1210.0,
        "qty_dinner": 1298.0,
        "total_qty": 2508.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 0.0,
        "total_qty": 6.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 1.0,
        "total_qty": 3.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 80,
        "qty_breakfast": 468.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 468.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 82,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1290.0,
        "total_qty": 1290.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 86,
        "qty_breakfast": 0.0,
        "qty_lunch": 311.0,
        "qty_dinner": 0.0,
        "total_qty": 311.0,
        "unit_price_ttc": 952.0
      },
      {
        "article_id": 91,
        "qty_breakfast": 1000.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 1000.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 1200.0,
        "qty_dinner": 1300.0,
        "total_qty": 2700.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 459,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 1202,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1286,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 88055.9,
    "lu_expense": 405799.75,
    "di_expense": 301568.625,
    "total_expense": 795424.275
  },
  {
    "date": "2026-10-07",
    "supply": [
      {
        "article_id": 5,
        "quantity": 215.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 7,
        "quantity": 24.0,
        "unit_price_ttc": 130.0
      },
      {
        "article_id": 9,
        "quantity": 93.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "quantity": 100.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "quantity": 404.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 14,
        "quantity": 255.0,
        "unit_price_ttc": 200.0
      },
      {
        "article_id": 21,
        "quantity": 264.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "quantity": 109.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 30,
        "quantity": 2.0,
        "unit_price_ttc": 400.0
      },
      {
        "article_id": 33,
        "quantity": 204.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 77,
        "quantity": 100.0,
        "unit_price_ttc": 571.1999999999999
      },
      {
        "article_id": 80,
        "quantity": 4800.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 81,
        "quantity": 17.535,
        "unit_price_ttc": 1190.0
      },
      {
        "article_id": 82,
        "quantity": 4800.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 83,
        "quantity": 800.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 96,
        "quantity": 1000.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "quantity": 2600.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 300.0,
        "total_qty": 300.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 1900.0,
        "qty_dinner": 0.0,
        "total_qty": 1900.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 48.0,
        "qty_dinner": 40.0,
        "total_qty": 88.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 7,
        "qty_breakfast": 0.0,
        "qty_lunch": 5.0,
        "qty_dinner": 5.0,
        "total_qty": 10.0,
        "unit_price_ttc": 130.0
      },
      {
        "article_id": 9,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 0.0,
        "total_qty": 30.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 55.0,
        "qty_dinner": 38.0,
        "total_qty": 93.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "qty_breakfast": 0.0,
        "qty_lunch": 200.0,
        "qty_dinner": 0.0,
        "total_qty": 200.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 0.0,
        "total_qty": 50.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "qty_breakfast": 0.0,
        "qty_lunch": 38.0,
        "qty_dinner": 0.0,
        "total_qty": 38.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 30,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 400.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 42.0,
        "qty_dinner": 35.0,
        "total_qty": 77.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 4.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 14.0,
        "qty_lunch": 5.0,
        "qty_dinner": 0.0,
        "total_qty": 19.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 12.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 12.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 4.0,
        "qty_dinner": 5.0,
        "total_qty": 9.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 43,
        "qty_breakfast": 0.0,
        "qty_lunch": 80.0,
        "qty_dinner": 0.0,
        "total_qty": 80.0,
        "unit_price_ttc": 348.8
      },
      {
        "article_id": 48,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 130.0,
        "total_qty": 130.0,
        "unit_price_ttc": 207.10000000000002
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 20.0,
        "total_qty": 20.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 52,
        "qty_breakfast": 0.0,
        "qty_lunch": 865.0,
        "qty_dinner": 1521.0,
        "total_qty": 2386.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 16.0,
        "qty_dinner": 18.0,
        "total_qty": 34.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 8.0,
        "total_qty": 14.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 60,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 0.0,
        "total_qty": 10.0,
        "unit_price_ttc": 487.9
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1520.0,
        "total_qty": 1520.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 7.0,
        "qty_dinner": 0.0,
        "total_qty": 7.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 2.0,
        "total_qty": 3.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 77,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 0.0,
        "total_qty": 30.0,
        "unit_price_ttc": 571.1999999999999
      },
      {
        "article_id": 79,
        "qty_breakfast": 375.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 375.0,
        "unit_price_ttc": 29.75
      },
      {
        "article_id": 80,
        "qty_breakfast": 70.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 70.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 83,
        "qty_breakfast": 60.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 60.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 96,
        "qty_breakfast": 1000.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 1000.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 900.0,
        "qty_dinner": 1500.0,
        "total_qty": 2600.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 439,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 852,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1513,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 94587.85,
    "lu_expense": 232595.85,
    "di_expense": 272188.25,
    "total_expense": 599371.95
  },
  {
    "date": "2026-10-08",
    "supply": [
      {
        "article_id": 3,
        "quantity": 650.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 42,
        "quantity": 200.0,
        "unit_price_ttc": 152.60000000000002
      },
      {
        "article_id": 50,
        "quantity": 18000.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 53,
        "quantity": 50.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 56,
        "quantity": 200.0,
        "unit_price_ttc": 618.8
      },
      {
        "article_id": 57,
        "quantity": 600.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 61,
        "quantity": 1000.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 63,
        "quantity": 15.0,
        "unit_price_ttc": 1190.0
      },
      {
        "article_id": 64,
        "quantity": 200.0,
        "unit_price_ttc": 559.3
      },
      {
        "article_id": 73,
        "quantity": 200.0,
        "unit_price_ttc": 1142.3999999999999
      },
      {
        "article_id": 97,
        "quantity": 1200.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "quantity": 2300.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [
      {
        "article_id": 52,
        "total_qty": 360.0,
        "unit_price_ttc": 17.849999999999998
      }
    ],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 20.0,
        "qty_dinner": 300.0,
        "total_qty": 320.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 210.0,
        "qty_dinner": 180.0,
        "total_qty": 390.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 88.0,
        "qty_dinner": 85.0,
        "total_qty": 173.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 9,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 33.0,
        "total_qty": 63.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 85.0,
        "qty_dinner": 75.0,
        "total_qty": 160.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 250.0,
        "total_qty": 250.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 65.0,
        "qty_dinner": 68.0,
        "total_qty": 133.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "qty_breakfast": 0.0,
        "qty_lunch": 68.0,
        "qty_dinner": 65.0,
        "total_qty": 133.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 55.0,
        "qty_dinner": 58.0,
        "total_qty": 113.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 5.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 5.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 15.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 15.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 14.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 14.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 5.0,
        "total_qty": 7.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 42,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 100.0,
        "total_qty": 100.0,
        "unit_price_ttc": 152.60000000000002
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 15.0,
        "total_qty": 15.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 2100.0,
        "qty_dinner": 180.0,
        "total_qty": 2280.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 52,
        "qty_breakfast": 0.0,
        "qty_lunch": 975.0,
        "qty_dinner": 1110.0,
        "total_qty": 2085.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 56,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 30.0,
        "total_qty": 60.0,
        "unit_price_ttc": 618.8
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 14.0,
        "qty_dinner": 16.0,
        "total_qty": 30.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 6.0,
        "total_qty": 12.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 60,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 10.0,
        "total_qty": 20.0,
        "unit_price_ttc": 487.9
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 64,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 10.0,
        "total_qty": 40.0,
        "unit_price_ttc": 559.3
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 7.0,
        "total_qty": 13.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 2.0,
        "total_qty": 3.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 73,
        "qty_breakfast": 0.0,
        "qty_lunch": 200.0,
        "qty_dinner": 0.0,
        "total_qty": 200.0,
        "unit_price_ttc": 1142.3999999999999
      },
      {
        "article_id": 77,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 20.0,
        "total_qty": 20.0,
        "unit_price_ttc": 571.1999999999999
      },
      {
        "article_id": 80,
        "qty_breakfast": 485.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 485.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 82,
        "qty_breakfast": 0.0,
        "qty_lunch": 968.0,
        "qty_dinner": 0.0,
        "total_qty": 968.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 83,
        "qty_breakfast": 65.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 65.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 97,
        "qty_breakfast": 1200.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 1200.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 1000.0,
        "qty_dinner": 1100.0,
        "total_qty": 2300.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 475,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 960,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1102,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 107155.4,
    "lu_expense": 625815.542,
    "di_expense": 407399.6,
    "total_expense": 1140370.542
  },
  {
    "date": "2026-10-09",
    "supply": [
      {
        "article_id": 95,
        "quantity": 900.0,
        "unit_price_ttc": 40.81
      },
      {
        "article_id": 98,
        "quantity": 2600.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 310.0,
        "qty_dinner": 20.0,
        "total_qty": 330.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 150.0,
        "qty_dinner": 150.0,
        "total_qty": 300.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 55.0,
        "qty_dinner": 69.0,
        "total_qty": 124.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 7,
        "qty_breakfast": 0.0,
        "qty_lunch": 14.0,
        "qty_dinner": 0.0,
        "total_qty": 14.0,
        "unit_price_ttc": 130.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 58.0,
        "qty_dinner": 42.0,
        "total_qty": 100.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 71.0,
        "total_qty": 71.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 60.0,
        "qty_dinner": 70.0,
        "total_qty": 130.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "qty_breakfast": 0.0,
        "qty_lunch": 65.0,
        "qty_dinner": 63.0,
        "total_qty": 128.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 52.0,
        "qty_dinner": 58.0,
        "total_qty": 110.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 4.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 12.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 12.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 10.0,
        "qty_lunch": 0.0,
        "qty_dinner": 12.0,
        "total_qty": 22.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 4.0,
        "qty_dinner": 3.0,
        "total_qty": 7.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 42,
        "qty_breakfast": 0.0,
        "qty_lunch": 15.0,
        "qty_dinner": 20.0,
        "total_qty": 35.0,
        "unit_price_ttc": 152.60000000000002
      },
      {
        "article_id": 45,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 10.0,
        "total_qty": 20.0,
        "unit_price_ttc": 403.3
      },
      {
        "article_id": 46,
        "qty_breakfast": 0.0,
        "qty_lunch": 120.0,
        "qty_dinner": 0.0,
        "total_qty": 120.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 47,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 110.0,
        "total_qty": 110.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 180.0,
        "qty_dinner": 2516.0,
        "total_qty": 2696.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 52,
        "qty_breakfast": 0.0,
        "qty_lunch": 723.0,
        "qty_dinner": 0.0,
        "total_qty": 723.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 38,
        "qty_breakfast": 4.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 56,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 30.0,
        "total_qty": 60.0,
        "unit_price_ttc": 618.8
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 16.0,
        "qty_dinner": 22.0,
        "total_qty": 38.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 6.0,
        "total_qty": 12.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 59,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 99.0,
        "total_qty": 99.0,
        "unit_price_ttc": 190.39999999999998
      },
      {
        "article_id": 60,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 0.0,
        "total_qty": 10.0,
        "unit_price_ttc": 487.9
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 63,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 15.0,
        "total_qty": 15.0,
        "unit_price_ttc": 1190.0
      },
      {
        "article_id": 64,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 25.0,
        "total_qty": 25.0,
        "unit_price_ttc": 559.3
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1181.0,
        "total_qty": 1181.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 3.0,
        "qty_dinner": 3.0,
        "total_qty": 6.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 6.0,
        "total_qty": 12.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 77,
        "qty_breakfast": 0.0,
        "qty_lunch": 15.0,
        "qty_dinner": 0.0,
        "total_qty": 15.0,
        "unit_price_ttc": 571.1999999999999
      },
      {
        "article_id": 80,
        "qty_breakfast": 392.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 392.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 82,
        "qty_breakfast": 0.0,
        "qty_lunch": 1158.0,
        "qty_dinner": 0.0,
        "total_qty": 1158.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 83,
        "qty_breakfast": 50.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 50.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 95,
        "qty_breakfast": 900.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 900.0,
        "unit_price_ttc": 40.81
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 1200.0,
        "qty_dinner": 1200.0,
        "total_qty": 2600.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 383,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 1150,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1168,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 88203.5,
    "lu_expense": 308159.32700000005,
    "di_expense": 516904.77999999997,
    "total_expense": 913267.6070000001
  },
  {
    "date": "2026-10-10",
    "supply": [
      {
        "article_id": 5,
        "quantity": 512.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 7,
        "quantity": 66.0,
        "unit_price_ttc": 130.0
      },
      {
        "article_id": 9,
        "quantity": 147.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "quantity": 806.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "quantity": 900.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 15,
        "quantity": 242.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 21,
        "quantity": 409.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "quantity": 415.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 33,
        "quantity": 489.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 51,
        "quantity": 200.0,
        "unit_price_ttc": 1737.3999999999999
      },
      {
        "article_id": 62,
        "quantity": 75.0,
        "unit_price_ttc": 1904.0
      },
      {
        "article_id": 74,
        "quantity": 20.0,
        "unit_price_ttc": 2975.0
      },
      {
        "article_id": 75,
        "quantity": 20.0,
        "unit_price_ttc": 1309.0
      },
      {
        "article_id": 96,
        "quantity": 600.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "quantity": 2500.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 240.0,
        "qty_dinner": 270.0,
        "total_qty": 510.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 63.0,
        "qty_dinner": 63.0,
        "total_qty": 126.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 7,
        "qty_breakfast": 0.0,
        "qty_lunch": 15.0,
        "qty_dinner": 0.0,
        "total_qty": 15.0,
        "unit_price_ttc": 130.0
      },
      {
        "article_id": 9,
        "qty_breakfast": 0.0,
        "qty_lunch": 65.0,
        "qty_dinner": 58.0,
        "total_qty": 123.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 75.0,
        "qty_dinner": 55.0,
        "total_qty": 130.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 300.0,
        "total_qty": 300.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 15,
        "qty_breakfast": 0.0,
        "qty_lunch": 45.0,
        "qty_dinner": 0.0,
        "total_qty": 45.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 65.0,
        "qty_dinner": 60.0,
        "total_qty": 125.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "qty_breakfast": 0.0,
        "qty_lunch": 60.0,
        "qty_dinner": 62.0,
        "total_qty": 122.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 52.0,
        "qty_dinner": 54.0,
        "total_qty": 106.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 3.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 3.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 10.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 10.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 10.0,
        "qty_lunch": 0.0,
        "qty_dinner": 20.0,
        "total_qty": 30.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 42,
        "qty_breakfast": 0.0,
        "qty_lunch": 15.0,
        "qty_dinner": 0.0,
        "total_qty": 15.0,
        "unit_price_ttc": 152.60000000000002
      },
      {
        "article_id": 48,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 120.0,
        "total_qty": 120.0,
        "unit_price_ttc": 207.10000000000002
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 180.0,
        "qty_dinner": 2840.0,
        "total_qty": 3020.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 51,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 30.0,
        "total_qty": 30.0,
        "unit_price_ttc": 1737.3999999999999
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 38,
        "qty_breakfast": 4.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 56,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 35.0,
        "total_qty": 65.0,
        "unit_price_ttc": 618.8
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 12.0,
        "qty_dinner": 14.0,
        "total_qty": 26.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 7.0,
        "total_qty": 13.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 60,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 10.0,
        "total_qty": 20.0,
        "unit_price_ttc": 487.9
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 62,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 30.0,
        "total_qty": 30.0,
        "unit_price_ttc": 1904.0
      },
      {
        "article_id": 64,
        "qty_breakfast": 0.0,
        "qty_lunch": 80.0,
        "qty_dinner": 0.0,
        "total_qty": 80.0,
        "unit_price_ttc": 559.3
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 1035.0,
        "qty_dinner": 0.0,
        "total_qty": 1035.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 3.0,
        "total_qty": 5.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 7.0,
        "qty_dinner": 6.0,
        "total_qty": 13.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 71,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 4.0,
        "total_qty": 4.0,
        "unit_price_ttc": 130.9
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 2.0,
        "total_qty": 3.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 77,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 0.0,
        "total_qty": 10.0,
        "unit_price_ttc": 571.1999999999999
      },
      {
        "article_id": 83,
        "qty_breakfast": 0.0,
        "qty_lunch": 210.0,
        "qty_dinner": 0.0,
        "total_qty": 210.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 96,
        "qty_breakfast": 600.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 600.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "qty_breakfast": 100.0,
        "qty_lunch": 1100.0,
        "qty_dinner": 1300.0,
        "total_qty": 2500.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 189,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 1029,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1300,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 44733.600000000006,
    "lu_expense": 237462.0,
    "di_expense": 690766.2999999999,
    "total_expense": 972961.8999999999
  },
  {
    "date": "2026-10-11",
    "supply": [
      {
        "article_id": 3,
        "quantity": 750.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 86,
        "quantity": 327.0,
        "unit_price_ttc": 952.0
      },
      {
        "article_id": 91,
        "quantity": 600.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "quantity": 2800.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 20.0,
        "qty_dinner": 410.0,
        "total_qty": 430.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 180.0,
        "qty_dinner": 900.0,
        "total_qty": 1080.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 58.0,
        "qty_dinner": 0.0,
        "total_qty": 58.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 9,
        "qty_breakfast": 0.0,
        "qty_lunch": 24.0,
        "qty_dinner": 0.0,
        "total_qty": 24.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 42.0,
        "qty_dinner": 234.0,
        "total_qty": 276.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 350.0,
        "total_qty": 350.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 15,
        "qty_breakfast": 0.0,
        "qty_lunch": 55.0,
        "qty_dinner": 38.0,
        "total_qty": 93.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 55.0,
        "qty_dinner": 0.0,
        "total_qty": 55.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "qty_breakfast": 0.0,
        "qty_lunch": 60.0,
        "qty_dinner": 0.0,
        "total_qty": 60.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 52.0,
        "qty_dinner": 42.0,
        "total_qty": 94.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 3.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 3.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 10.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 10.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 10.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 10.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 0.0,
        "total_qty": 10.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 47,
        "qty_breakfast": 0.0,
        "qty_lunch": 100.0,
        "qty_dinner": 0.0,
        "total_qty": 100.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 25.0,
        "total_qty": 25.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 180.0,
        "qty_dinner": 480.0,
        "total_qty": 660.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 38,
        "qty_breakfast": 3.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 3.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 56,
        "qty_breakfast": 0.0,
        "qty_lunch": 15.0,
        "qty_dinner": 0.0,
        "total_qty": 15.0,
        "unit_price_ttc": 618.8
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 14.0,
        "qty_dinner": 0.0,
        "total_qty": 14.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 8.0,
        "total_qty": 14.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 1070.0,
        "qty_dinner": 0.0,
        "total_qty": 1070.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 0.0,
        "total_qty": 2.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 77,
        "qty_breakfast": 0.0,
        "qty_lunch": 25.0,
        "qty_dinner": 0.0,
        "total_qty": 25.0,
        "unit_price_ttc": 571.1999999999999
      },
      {
        "article_id": 81,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 17.535,
        "total_qty": 17.535,
        "unit_price_ttc": 1190.0
      },
      {
        "article_id": 82,
        "qty_breakfast": 245.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 245.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 83,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 160.0,
        "total_qty": 160.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 86,
        "qty_breakfast": 0.0,
        "qty_lunch": 327.0,
        "qty_dinner": 0.0,
        "total_qty": 327.0,
        "unit_price_ttc": 952.0
      },
      {
        "article_id": 91,
        "qty_breakfast": 600.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 600.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "qty_breakfast": 100.0,
        "qty_lunch": 1100.0,
        "qty_dinner": 1600.0,
        "total_qty": 2800.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 244,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 1065,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1574,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 53454.2175,
    "lu_expense": 466415.7,
    "di_expense": 512819.55,
    "total_expense": 1032689.4675
  },
  {
    "date": "2026-10-12",
    "supply": [
      {
        "article_id": 89,
        "quantity": 1700.0,
        "unit_price_ttc": 46.648
      },
      {
        "article_id": 96,
        "quantity": 1200.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "quantity": 3000.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [
      {
        "article_id": 57,
        "total_qty": 60.0,
        "unit_price_ttc": 357.0
      }
    ],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 312.0,
        "qty_dinner": 0.0,
        "total_qty": 312.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 240.0,
        "qty_dinner": 270.0,
        "total_qty": 510.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 78.0,
        "qty_dinner": 75.0,
        "total_qty": 153.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 7,
        "qty_breakfast": 0.0,
        "qty_lunch": 11.0,
        "qty_dinner": 15.0,
        "total_qty": 26.0,
        "unit_price_ttc": 130.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 68.0,
        "qty_dinner": 52.0,
        "total_qty": 120.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 95.0,
        "total_qty": 95.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 14,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 255.0,
        "total_qty": 255.0,
        "unit_price_ttc": 200.0
      },
      {
        "article_id": 15,
        "qty_breakfast": 0.0,
        "qty_lunch": 24.0,
        "qty_dinner": 38.0,
        "total_qty": 62.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 65.0,
        "qty_dinner": 68.0,
        "total_qty": 133.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 49.0,
        "qty_dinner": 58.0,
        "total_qty": 107.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 5.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 5.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 14.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 14.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 13.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 13.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 4.0,
        "qty_dinner": 3.0,
        "total_qty": 7.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 42,
        "qty_breakfast": 0.0,
        "qty_lunch": 15.0,
        "qty_dinner": 15.0,
        "total_qty": 30.0,
        "unit_price_ttc": 152.60000000000002
      },
      {
        "article_id": 44,
        "qty_breakfast": 0.0,
        "qty_lunch": 110.0,
        "qty_dinner": 0.0,
        "total_qty": 110.0,
        "unit_price_ttc": 272.5
      },
      {
        "article_id": 47,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 150.0,
        "total_qty": 150.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 37,
        "qty_breakfast": 4.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 180.0,
        "qty_dinner": 3426.0,
        "total_qty": 3606.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 38,
        "qty_breakfast": 6.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 6.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 14.0,
        "qty_dinner": 24.0,
        "total_qty": 38.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 7.0,
        "qty_dinner": 7.0,
        "total_qty": 14.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 60,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 10.0,
        "total_qty": 20.0,
        "unit_price_ttc": 487.9
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 1.0,
        "total_qty": 3.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 7.0,
        "qty_dinner": 10.0,
        "total_qty": 17.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 2.0,
        "total_qty": 3.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 74,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 2975.0
      },
      {
        "article_id": 75,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 1309.0
      },
      {
        "article_id": 80,
        "qty_breakfast": 0.0,
        "qty_lunch": 1198.0,
        "qty_dinner": 0.0,
        "total_qty": 1198.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 83,
        "qty_breakfast": 65.0,
        "qty_lunch": 20.0,
        "qty_dinner": 0.0,
        "total_qty": 85.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 89,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1700.0,
        "total_qty": 1700.0,
        "unit_price_ttc": 46.648
      },
      {
        "article_id": 96,
        "qty_breakfast": 1200.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 1200.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 1200.0,
        "qty_dinner": 1600.0,
        "total_qty": 3000.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 516,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 1188,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1653,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 97540.20000000001,
    "lu_expense": 288146.30000000005,
    "di_expense": 670540.2999999999,
    "total_expense": 1056226.8
  },
  {
    "date": "2026-10-13",
    "supply": [
      {
        "article_id": 3,
        "quantity": 750.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 64,
        "quantity": 120.0,
        "unit_price_ttc": 559.3
      },
      {
        "article_id": 86,
        "quantity": 321.0,
        "unit_price_ttc": 952.0
      },
      {
        "article_id": 95,
        "quantity": 1400.0,
        "unit_price_ttc": 40.81
      },
      {
        "article_id": 98,
        "quantity": 3200.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [
      {
        "article_id": 67,
        "total_qty": 810.0,
        "unit_price_ttc": 26.18
      }
    ],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 15.0,
        "qty_dinner": 441.0,
        "total_qty": 456.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 180.0,
        "qty_dinner": 420.0,
        "total_qty": 600.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 45.0,
        "qty_dinner": 68.0,
        "total_qty": 113.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 7,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 25.0,
        "total_qty": 25.0,
        "unit_price_ttc": 130.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 40.0,
        "qty_dinner": 180.0,
        "total_qty": 220.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 360.0,
        "total_qty": 360.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 15,
        "qty_breakfast": 0.0,
        "qty_lunch": 20.0,
        "qty_dinner": 22.0,
        "total_qty": 42.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 47.0,
        "qty_dinner": 65.0,
        "total_qty": 112.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 42.0,
        "qty_dinner": 62.0,
        "total_qty": 104.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 5.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 5.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 15.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 15.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 14.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 14.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 5.0,
        "total_qty": 15.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 42,
        "qty_breakfast": 0.0,
        "qty_lunch": 20.0,
        "qty_dinner": 0.0,
        "total_qty": 20.0,
        "unit_price_ttc": 152.60000000000002
      },
      {
        "article_id": 47,
        "qty_breakfast": 0.0,
        "qty_lunch": 110.0,
        "qty_dinner": 0.0,
        "total_qty": 110.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 20.0,
        "total_qty": 20.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 37,
        "qty_breakfast": 6.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 6.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 240.0,
        "qty_dinner": 180.0,
        "total_qty": 420.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 3.0,
        "total_qty": 5.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 38,
        "qty_breakfast": 6.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 6.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 14.0,
        "qty_dinner": 24.0,
        "total_qty": 38.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 7.0,
        "qty_dinner": 7.0,
        "total_qty": 14.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 60,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 10.0,
        "total_qty": 20.0,
        "unit_price_ttc": 487.9
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 64,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 110.0,
        "total_qty": 110.0,
        "unit_price_ttc": 559.3
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 1298.0,
        "qty_dinner": 0.0,
        "total_qty": 1298.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 8.0,
        "qty_dinner": 8.0,
        "total_qty": 16.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 74,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 2975.0
      },
      {
        "article_id": 75,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 1309.0
      },
      {
        "article_id": 82,
        "qty_breakfast": 0.0,
        "qty_lunch": 580.0,
        "qty_dinner": 0.0,
        "total_qty": 580.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 86,
        "qty_breakfast": 0.0,
        "qty_lunch": 321.0,
        "qty_dinner": 0.0,
        "total_qty": 321.0,
        "unit_price_ttc": 952.0
      },
      {
        "article_id": 95,
        "qty_breakfast": 1400.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 1400.0,
        "unit_price_ttc": 40.81
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 1300.0,
        "qty_dinner": 1700.0,
        "total_qty": 3200.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 577,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 1295,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1701,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 103299.8,
    "lu_expense": 461404.61,
    "di_expense": 528068.7,
    "total_expense": 1092773.1099999999
  },
  {
    "date": "2026-10-14",
    "supply": [
      {
        "article_id": 5,
        "quantity": 215.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 7,
        "quantity": 23.0,
        "unit_price_ttc": 130.0
      },
      {
        "article_id": 10,
        "quantity": 335.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "quantity": 204.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 19,
        "quantity": 200.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 21,
        "quantity": 235.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "quantity": 146.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 30,
        "quantity": 2.0,
        "unit_price_ttc": 400.0
      },
      {
        "article_id": 33,
        "quantity": 254.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 90,
        "quantity": 1700.0,
        "unit_price_ttc": 75.8
      },
      {
        "article_id": 96,
        "quantity": 1400.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "quantity": 3100.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 294.0,
        "qty_dinner": 0.0,
        "total_qty": 294.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 180.0,
        "qty_dinner": 0.0,
        "total_qty": 180.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 58.0,
        "qty_dinner": 48.0,
        "total_qty": 106.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 7,
        "qty_breakfast": 0.0,
        "qty_lunch": 20.0,
        "qty_dinner": 3.0,
        "total_qty": 23.0,
        "unit_price_ttc": 130.0
      },
      {
        "article_id": 11,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 80.0,
        "total_qty": 80.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 60.0,
        "qty_dinner": 0.0,
        "total_qty": 60.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 48.0,
        "qty_dinner": 42.0,
        "total_qty": 90.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 5.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 5.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 15.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 15.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 18.0,
        "total_qty": 18.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 3.0,
        "total_qty": 5.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 43,
        "qty_breakfast": 0.0,
        "qty_lunch": 110.0,
        "qty_dinner": 0.0,
        "total_qty": 110.0,
        "unit_price_ttc": 348.8
      },
      {
        "article_id": 47,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 120.0,
        "total_qty": 120.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 37,
        "qty_breakfast": 10.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 10.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 180.0,
        "qty_dinner": 3332.0,
        "total_qty": 3512.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 51,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 40.0,
        "total_qty": 40.0,
        "unit_price_ttc": 1737.3999999999999
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 14.0,
        "qty_dinner": 22.0,
        "total_qty": 36.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 6.0,
        "total_qty": 12.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 60,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 10.0,
        "total_qty": 20.0,
        "unit_price_ttc": 487.9
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 62,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 30.0,
        "total_qty": 30.0,
        "unit_price_ttc": 1904.0
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1580.0,
        "total_qty": 1580.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 7.0,
        "qty_dinner": 0.0,
        "total_qty": 7.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 71,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 4.0,
        "total_qty": 4.0,
        "unit_price_ttc": 130.9
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 2.0,
        "total_qty": 3.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 74,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 2975.0
      },
      {
        "article_id": 75,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 1309.0
      },
      {
        "article_id": 80,
        "qty_breakfast": 592.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 592.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 83,
        "qty_breakfast": 75.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 75.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 90,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1700.0,
        "total_qty": 1700.0,
        "unit_price_ttc": 75.8
      },
      {
        "article_id": 96,
        "qty_breakfast": 1400.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 1400.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "qty_breakfast": 300.0,
        "qty_lunch": 1200.0,
        "qty_dinner": 1600.0,
        "total_qty": 3100.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 587,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 1184,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1576,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 126113.8,
    "lu_expense": 239225.1,
    "di_expense": 776925.5,
    "total_expense": 1142264.4
  },
  {
    "date": "2026-10-15",
    "supply": [
      {
        "article_id": 3,
        "quantity": 650.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "quantity": 6600.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 77,
        "quantity": 100.0,
        "unit_price_ttc": 571.1999999999999
      },
      {
        "article_id": 79,
        "quantity": 1200.0,
        "unit_price_ttc": 29.75
      },
      {
        "article_id": 80,
        "quantity": 4800.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 81,
        "quantity": 81.245,
        "unit_price_ttc": 1190.0
      },
      {
        "article_id": 82,
        "quantity": 4800.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 83,
        "quantity": 800.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 97,
        "quantity": 1400.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "quantity": 2700.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 20.0,
        "qty_dinner": 330.0,
        "total_qty": 350.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 628.0,
        "qty_dinner": 180.0,
        "total_qty": 808.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 49.0,
        "qty_dinner": 40.0,
        "total_qty": 89.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 68.0,
        "qty_dinner": 114.0,
        "total_qty": 182.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "qty_breakfast": 0.0,
        "qty_lunch": 269.0,
        "qty_dinner": 0.0,
        "total_qty": 269.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 60.0,
        "qty_dinner": 75.0,
        "total_qty": 135.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "qty_breakfast": 0.0,
        "qty_lunch": 78.0,
        "qty_dinner": 78.0,
        "total_qty": 156.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 30,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 400.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 62.0,
        "qty_dinner": 70.0,
        "total_qty": 132.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 4.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 14.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 14.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 10.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 10.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 4.0,
        "total_qty": 6.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 45,
        "qty_breakfast": 0.0,
        "qty_lunch": 110.0,
        "qty_dinner": 10.0,
        "total_qty": 120.0,
        "unit_price_ttc": 403.3
      },
      {
        "article_id": 48,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 120.0,
        "total_qty": 120.0,
        "unit_price_ttc": 207.10000000000002
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 15.0,
        "total_qty": 15.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 37,
        "qty_breakfast": 9.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 9.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 1806.0,
        "qty_dinner": 0.0,
        "total_qty": 1806.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 38,
        "qty_breakfast": 5.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 5.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 14.0,
        "qty_dinner": 20.0,
        "total_qty": 34.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 7.0,
        "total_qty": 13.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 60,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 10.0,
        "total_qty": 20.0,
        "unit_price_ttc": 487.9
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 64,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 10.0,
        "total_qty": 10.0,
        "unit_price_ttc": 559.3
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 2.0,
        "total_qty": 3.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 7.0,
        "total_qty": 13.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 2.0,
        "total_qty": 3.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 74,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 2975.0
      },
      {
        "article_id": 75,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 1309.0
      },
      {
        "article_id": 82,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1252.0,
        "total_qty": 1252.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 83,
        "qty_breakfast": 60.0,
        "qty_lunch": 20.0,
        "qty_dinner": 20.0,
        "total_qty": 100.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 97,
        "qty_breakfast": 1400.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 1400.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 1200.0,
        "qty_dinner": 1300.0,
        "total_qty": 2700.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 479,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 1127,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1249,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 108836.59999999998,
    "lu_expense": 457463.3,
    "di_expense": 292946.13800000004,
    "total_expense": 859246.038
  },
  {
    "date": "2026-10-16",
    "supply": [
      {
        "article_id": 95,
        "quantity": 700.0,
        "unit_price_ttc": 40.81
      },
      {
        "article_id": 98,
        "quantity": 2700.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 300.0,
        "qty_dinner": 0.0,
        "total_qty": 300.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 210.0,
        "qty_dinner": 2678.0,
        "total_qty": 2888.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 20.0,
        "qty_dinner": 20.0,
        "total_qty": 40.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 19,
        "qty_breakfast": 0.0,
        "qty_lunch": 200.0,
        "qty_dinner": 0.0,
        "total_qty": 200.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 35.0,
        "qty_dinner": 30.0,
        "total_qty": 65.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "qty_breakfast": 0.0,
        "qty_lunch": 78.0,
        "qty_dinner": 80.0,
        "total_qty": 158.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 65.0,
        "qty_dinner": 72.0,
        "total_qty": 137.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 3.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 3.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 12.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 12.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 8.0,
        "qty_lunch": 0.0,
        "qty_dinner": 16.0,
        "total_qty": 24.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 4.0,
        "qty_dinner": 2.0,
        "total_qty": 6.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 46,
        "qty_breakfast": 0.0,
        "qty_lunch": 120.0,
        "qty_dinner": 0.0,
        "total_qty": 120.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 50.0,
        "total_qty": 50.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 51,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 30.0,
        "total_qty": 30.0,
        "unit_price_ttc": 1737.3999999999999
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 38,
        "qty_breakfast": 5.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 5.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 16.0,
        "qty_dinner": 20.0,
        "total_qty": 36.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 6.0,
        "total_qty": 12.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 60,
        "qty_breakfast": 0.0,
        "qty_lunch": 5.0,
        "qty_dinner": 0.0,
        "total_qty": 5.0,
        "unit_price_ttc": 487.9
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 62,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 15.0,
        "total_qty": 15.0,
        "unit_price_ttc": 1904.0
      },
      {
        "article_id": 64,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 50.0,
        "total_qty": 50.0,
        "unit_price_ttc": 559.3
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 7.0,
        "qty_dinner": 7.0,
        "total_qty": 14.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 71,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 4.0,
        "total_qty": 4.0,
        "unit_price_ttc": 130.9
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 1.0,
        "total_qty": 3.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 74,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 2975.0
      },
      {
        "article_id": 75,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 1309.0
      },
      {
        "article_id": 77,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 20.0,
        "total_qty": 20.0,
        "unit_price_ttc": 571.1999999999999
      },
      {
        "article_id": 80,
        "qty_breakfast": 0.0,
        "qty_lunch": 1172.0,
        "qty_dinner": 0.0,
        "total_qty": 1172.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 82,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1238.0,
        "total_qty": 1238.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 83,
        "qty_breakfast": 35.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 35.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 95,
        "qty_breakfast": 700.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 700.0,
        "unit_price_ttc": 40.81
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 1200.0,
        "qty_dinner": 1300.0,
        "total_qty": 2700.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 257,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 1166,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1234,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 64187.4,
    "lu_expense": 324838.19999999995,
    "di_expense": 263324.897,
    "total_expense": 652350.497
  },
  {
    "date": "2026-10-17",
    "supply": [
      {
        "article_id": 5,
        "quantity": 206.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 7,
        "quantity": 24.0,
        "unit_price_ttc": 130.0
      },
      {
        "article_id": 9,
        "quantity": 112.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "quantity": 294.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "quantity": 396.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 15,
        "quantity": 110.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 21,
        "quantity": 103.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "quantity": 81.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 29,
        "quantity": 290.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 30,
        "quantity": 2.0,
        "unit_price_ttc": 400.0
      },
      {
        "article_id": 33,
        "quantity": 198.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "quantity": 100.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 36,
        "quantity": 200.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "quantity": 200.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 44,
        "quantity": 500.0,
        "unit_price_ttc": 272.5
      },
      {
        "article_id": 45,
        "quantity": 500.0,
        "unit_price_ttc": 403.3
      },
      {
        "article_id": 46,
        "quantity": 300.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 47,
        "quantity": 100.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 37,
        "quantity": 100.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 51,
        "quantity": 50.0,
        "unit_price_ttc": 1737.3999999999999
      },
      {
        "article_id": 53,
        "quantity": 60.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 56,
        "quantity": 335.0,
        "unit_price_ttc": 618.8
      },
      {
        "article_id": 57,
        "quantity": 500.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "quantity": 200.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 61,
        "quantity": 1000.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 62,
        "quantity": 50.0,
        "unit_price_ttc": 1904.0
      },
      {
        "article_id": 63,
        "quantity": 100.0,
        "unit_price_ttc": 1190.0
      },
      {
        "article_id": 65,
        "quantity": 300.0,
        "unit_price_ttc": 1142.3999999999999
      },
      {
        "article_id": 68,
        "quantity": 240.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 73,
        "quantity": 375.0,
        "unit_price_ttc": 1142.3999999999999
      },
      {
        "article_id": 96,
        "quantity": 600.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "quantity": 2900.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 210.0,
        "qty_dinner": 3590.0,
        "total_qty": 3800.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 58.0,
        "qty_dinner": 58.0,
        "total_qty": 116.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 9,
        "qty_breakfast": 0.0,
        "qty_lunch": 52.0,
        "qty_dinner": 58.0,
        "total_qty": 110.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 70.0,
        "qty_dinner": 160.0,
        "total_qty": 230.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 15,
        "qty_breakfast": 0.0,
        "qty_lunch": 35.0,
        "qty_dinner": 42.0,
        "total_qty": 77.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 59.0,
        "qty_dinner": 54.0,
        "total_qty": 113.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 29,
        "qty_breakfast": 0.0,
        "qty_lunch": 55.0,
        "qty_dinner": 60.0,
        "total_qty": 115.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 55.0,
        "qty_dinner": 60.0,
        "total_qty": 115.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 3.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 3.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 8.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 8.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 8.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 8.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 3.0,
        "total_qty": 5.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 20.0,
        "total_qty": 20.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 37,
        "qty_breakfast": 4.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 0.0,
        "total_qty": 2.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 38,
        "qty_breakfast": 3.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 3.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 16.0,
        "qty_dinner": 22.0,
        "total_qty": 38.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 6.0,
        "total_qty": 12.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 7.0,
        "qty_dinner": 7.0,
        "total_qty": 14.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 73,
        "qty_breakfast": 220.0,
        "qty_lunch": 30.0,
        "qty_dinner": 35.0,
        "total_qty": 285.0,
        "unit_price_ttc": 1142.3999999999999
      },
      {
        "article_id": 74,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 2975.0
      },
      {
        "article_id": 75,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 1309.0
      },
      {
        "article_id": 77,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 50.0,
        "total_qty": 50.0,
        "unit_price_ttc": 571.1999999999999
      },
      {
        "article_id": 79,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1200.0,
        "total_qty": 1200.0,
        "unit_price_ttc": 29.75
      },
      {
        "article_id": 80,
        "qty_breakfast": 0.0,
        "qty_lunch": 1225.0,
        "qty_dinner": 0.0,
        "total_qty": 1225.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 81,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 41.245,
        "total_qty": 41.245,
        "unit_price_ttc": 1190.0
      },
      {
        "article_id": 82,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 270.0,
        "total_qty": 270.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 83,
        "qty_breakfast": 25.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 25.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 96,
        "qty_breakfast": 600.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 600.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "qty_breakfast": 100.0,
        "qty_lunch": 1300.0,
        "qty_dinner": 1500.0,
        "total_qty": 2900.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 182,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 1219,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1467,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 301499.89999999997,
    "lu_expense": 131315.09999999998,
    "di_expense": 299329.155,
    "total_expense": 732144.155
  },
  {
    "date": "2026-10-18",
    "supply": [
      {
        "article_id": 3,
        "quantity": 800.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 86,
        "quantity": 339.0,
        "unit_price_ttc": 952.0
      },
      {
        "article_id": 89,
        "quantity": 1800.0,
        "unit_price_ttc": 46.648
      },
      {
        "article_id": 95,
        "quantity": 1400.0,
        "unit_price_ttc": 40.81
      },
      {
        "article_id": 98,
        "quantity": 3100.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 15.0,
        "qty_dinner": 440.0,
        "total_qty": 455.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 32.0,
        "qty_dinner": 51.0,
        "total_qty": 83.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 7,
        "qty_breakfast": 0.0,
        "qty_lunch": 12.0,
        "qty_dinner": 0.0,
        "total_qty": 12.0,
        "unit_price_ttc": 130.0
      },
      {
        "article_id": 9,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 0.0,
        "total_qty": 2.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 20.0,
        "qty_dinner": 0.0,
        "total_qty": 20.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 100.0,
        "total_qty": 100.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 15,
        "qty_breakfast": 0.0,
        "qty_lunch": 15.0,
        "qty_dinner": 18.0,
        "total_qty": 33.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 23,
        "qty_breakfast": 0.0,
        "qty_lunch": 13.0,
        "qty_dinner": 0.0,
        "total_qty": 13.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 29,
        "qty_breakfast": 0.0,
        "qty_lunch": 32.0,
        "qty_dinner": 0.0,
        "total_qty": 32.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 35.0,
        "qty_dinner": 40.0,
        "total_qty": 75.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 5.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 5.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 15.0,
        "qty_lunch": 0.0,
        "qty_dinner": 8.0,
        "total_qty": 23.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 12.0,
        "qty_lunch": 0.0,
        "qty_dinner": 20.0,
        "total_qty": 32.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 5.0,
        "total_qty": 15.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 47,
        "qty_breakfast": 0.0,
        "qty_lunch": 100.0,
        "qty_dinner": 0.0,
        "total_qty": 100.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 20.0,
        "total_qty": 20.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 37,
        "qty_breakfast": 8.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 8.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 51,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 40.0,
        "total_qty": 40.0,
        "unit_price_ttc": 1737.3999999999999
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 38,
        "qty_breakfast": 6.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 6.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 56,
        "qty_breakfast": 0.0,
        "qty_lunch": 25.0,
        "qty_dinner": 0.0,
        "total_qty": 25.0,
        "unit_price_ttc": 618.8
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 14.0,
        "qty_dinner": 10.0,
        "total_qty": 24.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 7.0,
        "total_qty": 13.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 62,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 40.0,
        "total_qty": 40.0,
        "unit_price_ttc": 1904.0
      },
      {
        "article_id": 65,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 140.0,
        "total_qty": 140.0,
        "unit_price_ttc": 1142.3999999999999
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 1082.0,
        "qty_dinner": 0.0,
        "total_qty": 1082.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 7.0,
        "qty_dinner": 0.0,
        "total_qty": 7.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 71,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 5.0,
        "total_qty": 5.0,
        "unit_price_ttc": 130.9
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 73,
        "qty_breakfast": 0.0,
        "qty_lunch": 15.0,
        "qty_dinner": 0.0,
        "total_qty": 15.0,
        "unit_price_ttc": 1142.3999999999999
      },
      {
        "article_id": 74,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 2975.0
      },
      {
        "article_id": 75,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 1309.0
      },
      {
        "article_id": 82,
        "qty_breakfast": 525.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1675.0,
        "total_qty": 2200.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 83,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 180.0,
        "total_qty": 180.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 86,
        "qty_breakfast": 0.0,
        "qty_lunch": 339.0,
        "qty_dinner": 0.0,
        "total_qty": 339.0,
        "unit_price_ttc": 952.0
      },
      {
        "article_id": 89,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1800.0,
        "total_qty": 1800.0,
        "unit_price_ttc": 46.648
      },
      {
        "article_id": 95,
        "qty_breakfast": 1400.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 1400.0,
        "unit_price_ttc": 40.81
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 1200.0,
        "qty_dinner": 1700.0,
        "total_qty": 3100.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 522,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 1076,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1673,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 116205.33750000001,
    "lu_expense": 450076.86,
    "di_expense": 765321.1625,
    "total_expense": 1331603.3599999999
  },
  {
    "date": "2026-10-19",
    "supply": [
      {
        "article_id": 77,
        "quantity": 50.0,
        "unit_price_ttc": 571.1999999999999
      },
      {
        "article_id": 80,
        "quantity": 2834.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 82,
        "quantity": 1450.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 83,
        "quantity": 420.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 96,
        "quantity": 1200.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "quantity": 2800.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 7,
        "qty_breakfast": 0.0,
        "qty_lunch": 12.0,
        "qty_dinner": 0.0,
        "total_qty": 12.0,
        "unit_price_ttc": 130.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 24.0,
        "qty_dinner": 0.0,
        "total_qty": 24.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 29,
        "qty_breakfast": 0.0,
        "qty_lunch": 63.0,
        "qty_dinner": 0.0,
        "total_qty": 63.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 20.0,
        "qty_dinner": 21.0,
        "total_qty": 41.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 5.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 5.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 14.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 14.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 12.0,
        "qty_lunch": 0.0,
        "qty_dinner": 20.0,
        "total_qty": 32.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 6.0,
        "total_qty": 8.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 44,
        "qty_breakfast": 0.0,
        "qty_lunch": 100.0,
        "qty_dinner": 0.0,
        "total_qty": 100.0,
        "unit_price_ttc": 272.5
      },
      {
        "article_id": 47,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 140.0,
        "total_qty": 140.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 37,
        "qty_breakfast": 6.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 6.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 51,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 40.0,
        "total_qty": 40.0,
        "unit_price_ttc": 1737.3999999999999
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 38,
        "qty_breakfast": 6.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 6.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 56,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 0.0,
        "total_qty": 30.0,
        "unit_price_ttc": 618.8
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 14.0,
        "qty_dinner": 18.0,
        "total_qty": 32.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 7.0,
        "total_qty": 13.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 62,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 10.0,
        "total_qty": 10.0,
        "unit_price_ttc": 1904.0
      },
      {
        "article_id": 63,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 30.0,
        "total_qty": 30.0,
        "unit_price_ttc": 1190.0
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 0.0,
        "total_qty": 6.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 73,
        "qty_breakfast": 0.0,
        "qty_lunch": 15.0,
        "qty_dinner": 15.0,
        "total_qty": 30.0,
        "unit_price_ttc": 1142.3999999999999
      },
      {
        "article_id": 74,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 2975.0
      },
      {
        "article_id": 75,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 1309.0
      },
      {
        "article_id": 80,
        "qty_breakfast": 0.0,
        "qty_lunch": 975.0,
        "qty_dinner": 0.0,
        "total_qty": 975.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 82,
        "qty_breakfast": 520.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 520.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 83,
        "qty_breakfast": 0.0,
        "qty_lunch": 320.0,
        "qty_dinner": 0.0,
        "total_qty": 320.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 96,
        "qty_breakfast": 1200.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 1200.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 1000.0,
        "qty_dinner": 1600.0,
        "total_qty": 2800.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 516,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 969,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1585,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 96191.18000000001,
    "lu_expense": 193153.3,
    "di_expense": 194906.7,
    "total_expense": 484251.18
  },
  {
    "date": "2026-10-20",
    "supply": [
      {
        "article_id": 3,
        "quantity": 800.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 47,
        "quantity": 100.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 48,
        "quantity": 500.0,
        "unit_price_ttc": 207.10000000000002
      },
      {
        "article_id": 50,
        "quantity": 12000.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 53,
        "quantity": 20.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 67,
        "quantity": 15000.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 72,
        "quantity": 120.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 75,
        "quantity": 40.0,
        "unit_price_ttc": 1309.0
      },
      {
        "article_id": 80,
        "quantity": 1966.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 83,
        "quantity": 380.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 86,
        "quantity": 337.0,
        "unit_price_ttc": 952.0
      },
      {
        "article_id": 95,
        "quantity": 1200.0,
        "unit_price_ttc": 40.81
      },
      {
        "article_id": 98,
        "quantity": 2800.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [
      {
        "article_id": 33,
        "quantity": 23.0,
        "unit_price_ttc": 65.0
      }
    ],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 400.0,
        "total_qty": 400.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 29,
        "qty_breakfast": 0.0,
        "qty_lunch": 40.0,
        "qty_dinner": 40.0,
        "total_qty": 80.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 30,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 400.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 13.0,
        "total_qty": 23.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 5.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 5.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 15.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 15.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 14.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 14.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 8.0,
        "qty_dinner": 4.0,
        "total_qty": 12.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 47,
        "qty_breakfast": 0.0,
        "qty_lunch": 100.0,
        "qty_dinner": 0.0,
        "total_qty": 100.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 48,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 140.0,
        "total_qty": 140.0,
        "unit_price_ttc": 207.10000000000002
      },
      {
        "article_id": 37,
        "qty_breakfast": 8.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 8.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 180.0,
        "qty_dinner": 240.0,
        "total_qty": 420.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 38,
        "qty_breakfast": 7.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 7.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 56,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 40.0,
        "total_qty": 70.0,
        "unit_price_ttc": 618.8
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 11.0,
        "qty_dinner": 22.0,
        "total_qty": 33.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 8.0,
        "total_qty": 14.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 972.0,
        "qty_dinner": 0.0,
        "total_qty": 972.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 8.0,
        "total_qty": 14.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 73,
        "qty_breakfast": 0.0,
        "qty_lunch": 15.0,
        "qty_dinner": 30.0,
        "total_qty": 45.0,
        "unit_price_ttc": 1142.3999999999999
      },
      {
        "article_id": 74,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 2975.0
      },
      {
        "article_id": 75,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 1309.0
      },
      {
        "article_id": 77,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 20.0,
        "total_qty": 20.0,
        "unit_price_ttc": 571.1999999999999
      },
      {
        "article_id": 80,
        "qty_breakfast": 545.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1520.0,
        "total_qty": 2065.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 86,
        "qty_breakfast": 0.0,
        "qty_lunch": 337.0,
        "qty_dinner": 0.0,
        "total_qty": 337.0,
        "unit_price_ttc": 952.0
      },
      {
        "article_id": 95,
        "qty_breakfast": 1200.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 1200.0,
        "unit_price_ttc": 40.81
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 1000.0,
        "qty_dinner": 1600.0,
        "total_qty": 2800.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 540,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 966,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1513,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 107357.7,
    "lu_expense": 449446.06,
    "di_expense": 383708.3,
    "total_expense": 940512.06
  },
  {
    "date": "2026-10-21",
    "supply": [
      {
        "article_id": 5,
        "quantity": 194.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 7,
        "quantity": 33.0,
        "unit_price_ttc": 130.0
      },
      {
        "article_id": 9,
        "quantity": 118.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "quantity": 159.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "quantity": 400.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 15,
        "quantity": 87.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 21,
        "quantity": 100.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "quantity": 138.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 33,
        "quantity": 190.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 90,
        "quantity": 1600.0,
        "unit_price_ttc": 75.8
      },
      {
        "article_id": 96,
        "quantity": 1400.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "quantity": 2600.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 280.0,
        "qty_dinner": 30.0,
        "total_qty": 310.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 32.0,
        "qty_dinner": 25.0,
        "total_qty": 57.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 7,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 9.0,
        "total_qty": 19.0,
        "unit_price_ttc": 130.0
      },
      {
        "article_id": 9,
        "qty_breakfast": 0.0,
        "qty_lunch": 35.0,
        "qty_dinner": 0.0,
        "total_qty": 35.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 38.0,
        "qty_dinner": 80.0,
        "total_qty": 118.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 100.0,
        "total_qty": 100.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 15,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 10.0,
        "total_qty": 10.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 42.0,
        "qty_dinner": 0.0,
        "total_qty": 42.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "qty_breakfast": 0.0,
        "qty_lunch": 40.0,
        "qty_dinner": 0.0,
        "total_qty": 40.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 35.0,
        "qty_dinner": 20.0,
        "total_qty": 55.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 5.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 5.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 15.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 15.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 12.0,
        "qty_lunch": 0.0,
        "qty_dinner": 20.0,
        "total_qty": 32.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 4.0,
        "qty_dinner": 3.0,
        "total_qty": 7.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 43,
        "qty_breakfast": 0.0,
        "qty_lunch": 100.0,
        "qty_dinner": 0.0,
        "total_qty": 100.0,
        "unit_price_ttc": 348.8
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 20.0,
        "total_qty": 20.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 37,
        "qty_breakfast": 8.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 8.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 180.0,
        "qty_dinner": 2964.0,
        "total_qty": 3144.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 51,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 40.0,
        "total_qty": 40.0,
        "unit_price_ttc": 1737.3999999999999
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 38,
        "qty_breakfast": 6.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 6.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 56,
        "qty_breakfast": 0.0,
        "qty_lunch": 25.0,
        "qty_dinner": 0.0,
        "total_qty": 25.0,
        "unit_price_ttc": 618.8
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 12.0,
        "qty_dinner": 10.0,
        "total_qty": 22.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 7.0,
        "total_qty": 13.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 63,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 30.0,
        "total_qty": 30.0,
        "unit_price_ttc": 1190.0
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1382.0,
        "total_qty": 1382.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 8.0,
        "total_qty": 14.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 71,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 5.0,
        "total_qty": 5.0,
        "unit_price_ttc": 130.9
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 73,
        "qty_breakfast": 0.0,
        "qty_lunch": 15.0,
        "qty_dinner": 50.0,
        "total_qty": 65.0,
        "unit_price_ttc": 1142.3999999999999
      },
      {
        "article_id": 74,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 2975.0
      },
      {
        "article_id": 75,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 1309.0
      },
      {
        "article_id": 77,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 30.0,
        "total_qty": 30.0,
        "unit_price_ttc": 571.1999999999999
      },
      {
        "article_id": 80,
        "qty_breakfast": 0.0,
        "qty_lunch": 935.0,
        "qty_dinner": 0.0,
        "total_qty": 935.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 81,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 40.0,
        "total_qty": 40.0,
        "unit_price_ttc": 1190.0
      },
      {
        "article_id": 83,
        "qty_breakfast": 70.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 70.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 90,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1600.0,
        "total_qty": 1600.0,
        "unit_price_ttc": 75.8
      },
      {
        "article_id": 96,
        "qty_breakfast": 1400.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 1400.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 1000.0,
        "qty_dinner": 1400.0,
        "total_qty": 2600.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 583,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 927,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1377,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 111592.6,
    "lu_expense": 284607.1,
    "di_expense": 833455.1599999999,
    "total_expense": 1229654.8599999999
  },
  {
    "date": "2026-10-22",
    "supply": [
      {
        "article_id": 3,
        "quantity": 800.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "quantity": 12000.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 97,
        "quantity": 1300.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "quantity": 3000.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 25.0,
        "qty_dinner": 370.0,
        "total_qty": 395.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 300.0,
        "qty_dinner": 600.0,
        "total_qty": 900.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 48.0,
        "qty_dinner": 39.0,
        "total_qty": 87.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 9,
        "qty_breakfast": 0.0,
        "qty_lunch": 33.0,
        "qty_dinner": 0.0,
        "total_qty": 33.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 18.0,
        "qty_dinner": 0.0,
        "total_qty": 18.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 300.0,
        "total_qty": 300.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 15,
        "qty_breakfast": 0.0,
        "qty_lunch": 20.0,
        "qty_dinner": 15.0,
        "total_qty": 35.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 28.0,
        "qty_dinner": 0.0,
        "total_qty": 28.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "qty_breakfast": 0.0,
        "qty_lunch": 38.0,
        "qty_dinner": 0.0,
        "total_qty": 38.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 35.0,
        "qty_dinner": 35.0,
        "total_qty": 70.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 5.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 5.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 15.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 15.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 12.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 12.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 5.0,
        "total_qty": 7.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 45,
        "qty_breakfast": 0.0,
        "qty_lunch": 120.0,
        "qty_dinner": 0.0,
        "total_qty": 120.0,
        "unit_price_ttc": 403.3
      },
      {
        "article_id": 47,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 140.0,
        "total_qty": 140.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 20.0,
        "total_qty": 20.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 37,
        "qty_breakfast": 6.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 6.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 2610.0,
        "qty_dinner": 0.0,
        "total_qty": 2610.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 38,
        "qty_breakfast": 6.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 6.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 56,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 0.0,
        "total_qty": 30.0,
        "unit_price_ttc": 618.8
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 14.0,
        "qty_dinner": 22.0,
        "total_qty": 36.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 7.0,
        "total_qty": 13.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 7.0,
        "total_qty": 13.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 2.0,
        "total_qty": 3.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 75,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 1309.0
      },
      {
        "article_id": 80,
        "qty_breakfast": 0.0,
        "qty_lunch": 1220.0,
        "qty_dinner": 0.0,
        "total_qty": 1220.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 82,
        "qty_breakfast": 517.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 517.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 83,
        "qty_breakfast": 0.0,
        "qty_lunch": 20.0,
        "qty_dinner": 0.0,
        "total_qty": 20.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 97,
        "qty_breakfast": 1300.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 1300.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 1300.0,
        "qty_dinner": 1500.0,
        "total_qty": 3000.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 515,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 2215,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1414,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 103126.2855,
    "lu_expense": 471725.3,
    "di_expense": 368805.7,
    "total_expense": 943657.2855
  },
  {
    "date": "2026-10-23",
    "supply": [
      {
        "article_id": 95,
        "quantity": 1200.0,
        "unit_price_ttc": 40.81
      },
      {
        "article_id": 98,
        "quantity": 2900.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 380.0,
        "qty_dinner": 30.0,
        "total_qty": 410.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 300.0,
        "qty_dinner": 600.0,
        "total_qty": 900.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 20.0,
        "total_qty": 50.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 7,
        "qty_breakfast": 0.0,
        "qty_lunch": 14.0,
        "qty_dinner": 0.0,
        "total_qty": 14.0,
        "unit_price_ttc": 130.0
      },
      {
        "article_id": 9,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 0.0,
        "total_qty": 50.0,
        "unit_price_ttc": 125.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 23.0,
        "qty_dinner": 0.0,
        "total_qty": 23.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 14,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 40.0,
        "total_qty": 40.0,
        "unit_price_ttc": 200.0
      },
      {
        "article_id": 15,
        "qty_breakfast": 0.0,
        "qty_lunch": 19.0,
        "qty_dinner": 15.0,
        "total_qty": 34.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 16,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 30.0,
        "total_qty": 30.0,
        "unit_price_ttc": 260.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 0.0,
        "total_qty": 30.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "qty_breakfast": 0.0,
        "qty_lunch": 60.0,
        "qty_dinner": 0.0,
        "total_qty": 60.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 35.0,
        "qty_dinner": 30.0,
        "total_qty": 65.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 5.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 5.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 14.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 14.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 20.0,
        "total_qty": 20.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 5.0,
        "qty_dinner": 3.0,
        "total_qty": 8.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 46,
        "qty_breakfast": 0.0,
        "qty_lunch": 140.0,
        "qty_dinner": 0.0,
        "total_qty": 140.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 48,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 120.0,
        "total_qty": 120.0,
        "unit_price_ttc": 207.10000000000002
      },
      {
        "article_id": 37,
        "qty_breakfast": 8.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 8.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 240.0,
        "qty_dinner": 2440.0,
        "total_qty": 2680.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 38,
        "qty_breakfast": 6.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 6.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 56,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 0.0,
        "total_qty": 30.0,
        "unit_price_ttc": 618.8
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 14.0,
        "qty_dinner": 22.0,
        "total_qty": 36.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 7.0,
        "total_qty": 13.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1225.0,
        "total_qty": 1225.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 3.0,
        "qty_dinner": 3.0,
        "total_qty": 6.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 6.0,
        "total_qty": 12.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 71,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 5.0,
        "total_qty": 5.0,
        "unit_price_ttc": 130.9
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 3.0,
        "qty_dinner": 2.0,
        "total_qty": 5.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 75,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 1309.0
      },
      {
        "article_id": 80,
        "qty_breakfast": 0.0,
        "qty_lunch": 1390.0,
        "qty_dinner": 0.0,
        "total_qty": 1390.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 82,
        "qty_breakfast": 485.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 485.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 83,
        "qty_breakfast": 60.0,
        "qty_lunch": 30.0,
        "qty_dinner": 0.0,
        "total_qty": 90.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 95,
        "qty_breakfast": 1200.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 1200.0,
        "unit_price_ttc": 40.81
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 1400.0,
        "qty_dinner": 1300.0,
        "total_qty": 2900.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 481,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 1382,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1216,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 115769.8775,
    "lu_expense": 334940.89999999997,
    "di_expense": 421509.7,
    "total_expense": 872220.4775
  },
  {
    "date": "2026-10-24",
    "supply": [
      {
        "article_id": 5,
        "quantity": 199.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 7,
        "quantity": 14.0,
        "unit_price_ttc": 130.0
      },
      {
        "article_id": 10,
        "quantity": 138.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "quantity": 401.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 15,
        "quantity": 209.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 21,
        "quantity": 231.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "quantity": 251.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 33,
        "quantity": 252.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 52,
        "quantity": 6048.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 91,
        "quantity": 1200.0,
        "unit_price_ttc": 46.64
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 35.0,
        "total_qty": 65.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 2242.0,
        "qty_dinner": 0.0,
        "total_qty": 2242.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 32.0,
        "total_qty": 62.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 38.0,
        "qty_dinner": 28.0,
        "total_qty": 66.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 15,
        "qty_breakfast": 0.0,
        "qty_lunch": 38.0,
        "qty_dinner": 35.0,
        "total_qty": 73.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 40.0,
        "qty_dinner": 0.0,
        "total_qty": 40.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "qty_breakfast": 0.0,
        "qty_lunch": 48.0,
        "qty_dinner": 0.0,
        "total_qty": 48.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 35.0,
        "qty_dinner": 38.0,
        "total_qty": 73.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 4.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 14.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 14.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 12.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 12.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 44,
        "qty_breakfast": 0.0,
        "qty_lunch": 100.0,
        "qty_dinner": 0.0,
        "total_qty": 100.0,
        "unit_price_ttc": 272.5
      },
      {
        "article_id": 47,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 140.0,
        "total_qty": 140.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 20.0,
        "total_qty": 20.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 37,
        "qty_breakfast": 8.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 8.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 180.0,
        "qty_dinner": 2928.0,
        "total_qty": 3108.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 52,
        "qty_breakfast": 0.0,
        "qty_lunch": 995.0,
        "qty_dinner": 1476.0,
        "total_qty": 2471.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 2.0,
        "total_qty": 3.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 56,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 0.0,
        "total_qty": 30.0,
        "unit_price_ttc": 618.8
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 12.0,
        "qty_dinner": 22.0,
        "total_qty": 34.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 6.0,
        "total_qty": 12.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1474.0,
        "total_qty": 1474.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 3.0,
        "total_qty": 4.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 0.0,
        "total_qty": 6.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 2.0,
        "total_qty": 3.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 75,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 1309.0
      },
      {
        "article_id": 80,
        "qty_breakfast": 0.0,
        "qty_lunch": 992.0,
        "qty_dinner": 0.0,
        "total_qty": 992.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 82,
        "qty_breakfast": 448.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 448.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 83,
        "qty_breakfast": 58.0,
        "qty_lunch": 30.0,
        "qty_dinner": 0.0,
        "total_qty": 88.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 91,
        "qty_breakfast": 1200.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 1200.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 1000.0,
        "qty_dinner": 1500.0,
        "total_qty": 2700.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 440,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 986,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1464,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 112939.79199999999,
    "lu_expense": 204646.25,
    "di_expense": 494225.01999999996,
    "total_expense": 811811.0619999999
  },
  {
    "date": "2026-10-25",
    "supply": [
      {
        "article_id": 3,
        "quantity": 800.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 86,
        "quantity": 348.0,
        "unit_price_ttc": 952.0
      },
      {
        "article_id": 91,
        "quantity": 1400.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "quantity": 3000.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [
      {
        "article_id": 65,
        "total_qty": 60.0,
        "unit_price_ttc": 1142.3999999999999
      }
    ],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 20.0,
        "qty_dinner": 400.0,
        "total_qty": 420.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 300.0,
        "qty_dinner": 600.0,
        "total_qty": 900.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 40.0,
        "qty_dinner": 38.0,
        "total_qty": 78.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 15,
        "qty_breakfast": 0.0,
        "qty_lunch": 32.0,
        "qty_dinner": 32.0,
        "total_qty": 64.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 45.0,
        "qty_dinner": 0.0,
        "total_qty": 45.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "qty_breakfast": 0.0,
        "qty_lunch": 48.0,
        "qty_dinner": 0.0,
        "total_qty": 48.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 35.0,
        "qty_dinner": 35.0,
        "total_qty": 70.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 5.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 5.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 15.0,
        "qty_lunch": 0.0,
        "qty_dinner": 6.0,
        "total_qty": 21.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 14.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 14.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 5.0,
        "total_qty": 15.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 47,
        "qty_breakfast": 0.0,
        "qty_lunch": 120.0,
        "qty_dinner": 0.0,
        "total_qty": 120.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 20.0,
        "total_qty": 20.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 37,
        "qty_breakfast": 8.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 8.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 38.0,
        "qty_dinner": 0.0,
        "total_qty": 38.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 52,
        "qty_breakfast": 0.0,
        "qty_lunch": 1238.0,
        "qty_dinner": 1104.0,
        "total_qty": 2342.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 38,
        "qty_breakfast": 6.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 6.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 56,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 0.0,
        "total_qty": 30.0,
        "unit_price_ttc": 618.8
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 14.0,
        "qty_dinner": 24.0,
        "total_qty": 38.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 7.0,
        "qty_dinner": 7.0,
        "total_qty": 14.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 65,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 100.0,
        "total_qty": 100.0,
        "unit_price_ttc": 1142.3999999999999
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 1235.0,
        "qty_dinner": 0.0,
        "total_qty": 1235.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 8.0,
        "qty_dinner": 0.0,
        "total_qty": 8.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 1.0,
        "total_qty": 3.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 75,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 1309.0
      },
      {
        "article_id": 80,
        "qty_breakfast": 560.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 560.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 82,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1505.0,
        "total_qty": 1505.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 83,
        "qty_breakfast": 68.0,
        "qty_lunch": 25.0,
        "qty_dinner": 80.0,
        "total_qty": 173.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 86,
        "qty_breakfast": 0.0,
        "qty_lunch": 348.0,
        "qty_dinner": 0.0,
        "total_qty": 348.0,
        "unit_price_ttc": 952.0
      },
      {
        "article_id": 89,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1700.0,
        "total_qty": 1700.0,
        "unit_price_ttc": 46.648
      },
      {
        "article_id": 91,
        "qty_breakfast": 1400.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 1400.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 1300.0,
        "qty_dinner": 1500.0,
        "total_qty": 3000.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 557,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 1230,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1501,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 132826.08000000002,
    "lu_expense": 492089.3,
    "di_expense": 507180.9075,
    "total_expense": 1132096.2875
  },
  {
    "date": "2026-10-26",
    "supply": [
      {
        "article_id": 77,
        "quantity": 100.0,
        "unit_price_ttc": 571.1999999999999
      },
      {
        "article_id": 80,
        "quantity": 2400.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 83,
        "quantity": 800.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 96,
        "quantity": 1000.0,
        "unit_price_ttc": 46.64
      }
    ],
    "loan_in": [
      {
        "article_id": 98,
        "quantity": 3000.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_out": [
      {
        "article_id": 67,
        "total_qty": 4617.0,
        "unit_price_ttc": 26.18
      }
    ],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 25.0,
        "qty_dinner": 375.0,
        "total_qty": 400.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 2654.0,
        "qty_dinner": 0.0,
        "total_qty": 2654.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 19.0,
        "qty_dinner": 18.0,
        "total_qty": 37.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 22.0,
        "qty_dinner": 15.0,
        "total_qty": 37.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 11,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 301.0,
        "total_qty": 301.0,
        "unit_price_ttc": 430.0
      },
      {
        "article_id": 15,
        "qty_breakfast": 0.0,
        "qty_lunch": 22.0,
        "qty_dinner": 13.0,
        "total_qty": 35.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 46.0,
        "qty_dinner": 0.0,
        "total_qty": 46.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "qty_breakfast": 0.0,
        "qty_lunch": 55.0,
        "qty_dinner": 0.0,
        "total_qty": 55.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 29.0,
        "qty_dinner": 18.0,
        "total_qty": 47.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 4.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 12.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 12.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 10.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 10.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 5.0,
        "total_qty": 7.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 44,
        "qty_breakfast": 0.0,
        "qty_lunch": 120.0,
        "qty_dinner": 0.0,
        "total_qty": 120.0,
        "unit_price_ttc": 272.5
      },
      {
        "article_id": 48,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 150.0,
        "total_qty": 150.0,
        "unit_price_ttc": 207.10000000000002
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 20.0,
        "total_qty": 20.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 37,
        "qty_breakfast": 5.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 5.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 52,
        "qty_breakfast": 0.0,
        "qty_lunch": 1235.0,
        "qty_dinner": 0.0,
        "total_qty": 1235.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 14.0,
        "qty_dinner": 22.0,
        "total_qty": 36.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 7.0,
        "total_qty": 13.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 50.0,
        "total_qty": 100.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 3.0,
        "total_qty": 5.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 7.0,
        "qty_dinner": 7.0,
        "total_qty": 14.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 2.0,
        "total_qty": 3.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 75,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 1309.0
      },
      {
        "article_id": 80,
        "qty_breakfast": 0.0,
        "qty_lunch": 1175.0,
        "qty_dinner": 0.0,
        "total_qty": 1175.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 83,
        "qty_breakfast": 40.0,
        "qty_lunch": 30.0,
        "qty_dinner": 0.0,
        "total_qty": 70.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 92,
        "qty_breakfast": 1000.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 1000.0,
        "unit_price_ttc": 8.5
      },
      {
        "article_id": 98,
        "qty_breakfast": 100.0,
        "qty_lunch": 1200.0,
        "qty_dinner": 1600.0,
        "total_qty": 2900.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 317,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 1174,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1515,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 39380.9,
    "lu_expense": 184129.65,
    "di_expense": 373473.7,
    "total_expense": 596984.25
  },
  {
    "date": "2026-10-27",
    "supply": [
      {
        "article_id": 3,
        "quantity": 900.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 34,
        "quantity": 100.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 36,
        "quantity": 200.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 42,
        "quantity": 400.0,
        "unit_price_ttc": 152.60000000000002
      },
      {
        "article_id": 44,
        "quantity": 500.0,
        "unit_price_ttc": 272.5
      },
      {
        "article_id": 45,
        "quantity": 500.0,
        "unit_price_ttc": 403.3
      },
      {
        "article_id": 46,
        "quantity": 300.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 37,
        "quantity": 100.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 50,
        "quantity": 12000.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 53,
        "quantity": 60.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 56,
        "quantity": 500.0,
        "unit_price_ttc": 618.8
      },
      {
        "article_id": 57,
        "quantity": 500.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 65,
        "quantity": 300.0,
        "unit_price_ttc": 1142.3999999999999
      },
      {
        "article_id": 68,
        "quantity": 240.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 73,
        "quantity": 300.0,
        "unit_price_ttc": 1142.3999999999999
      },
      {
        "article_id": 86,
        "quantity": 341.0,
        "unit_price_ttc": 952.0
      },
      {
        "article_id": 95,
        "quantity": 1400.0,
        "unit_price_ttc": 40.81
      },
      {
        "article_id": 98,
        "quantity": 2900.0,
        "unit_price_ttc": 7.5
      }
    ],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 380.0,
        "total_qty": 410.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 300.0,
        "qty_dinner": 900.0,
        "total_qty": 1200.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 16.0,
        "qty_dinner": 6.0,
        "total_qty": 22.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 15.0,
        "qty_dinner": 20.0,
        "total_qty": 35.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 15,
        "qty_breakfast": 0.0,
        "qty_lunch": 20.0,
        "qty_dinner": 17.0,
        "total_qty": 37.0,
        "unit_price_ttc": 110.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 35.0,
        "qty_dinner": 30.0,
        "total_qty": 65.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "qty_breakfast": 0.0,
        "qty_lunch": 38.0,
        "qty_dinner": 35.0,
        "total_qty": 73.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 18.0,
        "qty_dinner": 30.0,
        "total_qty": 48.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 5.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 5.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 15.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 15.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 14.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 14.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 4.0,
        "total_qty": 14.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 42,
        "qty_breakfast": 120.0,
        "qty_lunch": 0.0,
        "qty_dinner": 50.0,
        "total_qty": 170.0,
        "unit_price_ttc": 152.60000000000002
      },
      {
        "article_id": 45,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 15.0,
        "total_qty": 25.0,
        "unit_price_ttc": 403.3
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 20.0,
        "total_qty": 20.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 37,
        "qty_breakfast": 8.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 8.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 240.0,
        "qty_dinner": 360.0,
        "total_qty": 600.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 3.0,
        "qty_dinner": 3.0,
        "total_qty": 6.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 38,
        "qty_breakfast": 7.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 7.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 56,
        "qty_breakfast": 0.0,
        "qty_lunch": 35.0,
        "qty_dinner": 45.0,
        "total_qty": 80.0,
        "unit_price_ttc": 618.8
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 12.0,
        "qty_dinner": 22.0,
        "total_qty": 34.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 7.0,
        "total_qty": 13.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 61,
        "qty_breakfast": 0.0,
        "qty_lunch": 50.0,
        "qty_dinner": 0.0,
        "total_qty": 50.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 1165.0,
        "qty_dinner": 0.0,
        "total_qty": 1165.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 3.0,
        "qty_dinner": 4.0,
        "total_qty": 7.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 8.0,
        "total_qty": 14.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 3.0,
        "qty_dinner": 3.0,
        "total_qty": 6.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 73,
        "qty_breakfast": 250.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 250.0,
        "unit_price_ttc": 1142.3999999999999
      },
      {
        "article_id": 75,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 2.0,
        "total_qty": 3.0,
        "unit_price_ttc": 1309.0
      },
      {
        "article_id": 77,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 50.0,
        "total_qty": 50.0,
        "unit_price_ttc": 571.1999999999999
      },
      {
        "article_id": 80,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1395.0,
        "total_qty": 1395.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 82,
        "qty_breakfast": 545.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 545.0,
        "unit_price_ttc": 22.4315
      },
      {
        "article_id": 86,
        "qty_breakfast": 0.0,
        "qty_lunch": 341.0,
        "qty_dinner": 0.0,
        "total_qty": 341.0,
        "unit_price_ttc": 952.0
      },
      {
        "article_id": 95,
        "qty_breakfast": 1400.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 1400.0,
        "unit_price_ttc": 40.81
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 1200.0,
        "qty_dinner": 1500.0,
        "total_qty": 2900.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 542,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 1158,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 1389,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 421019.6675,
    "lu_expense": 470818.80000000005,
    "di_expense": 384730.7,
    "total_expense": 1276569.1675
  },
  {
    "date": "2026-10-28",
    "supply": [],
    "loan_in": [],
    "loan_out": [
      {
        "article_id": 39,
        "total_qty": 10.0,
        "unit_price_ttc": 600.0
      }
    ],
    "kitchen": [
      {
        "article_id": 1,
        "qty_breakfast": 0.0,
        "qty_lunch": 25.0,
        "qty_dinner": 240.0,
        "total_qty": 265.0,
        "unit_price_ttc": 1595.0
      },
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 270.0,
        "qty_dinner": 30.0,
        "total_qty": 300.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 270.0,
        "qty_dinner": 900.0,
        "total_qty": 1170.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 45.0,
        "qty_dinner": 42.0,
        "total_qty": 87.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 35.0,
        "qty_dinner": 40.0,
        "total_qty": 75.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 35.0,
        "qty_dinner": 0.0,
        "total_qty": 35.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "qty_breakfast": 0.0,
        "qty_lunch": 55.0,
        "qty_dinner": 0.0,
        "total_qty": 55.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 22.0,
        "qty_dinner": 38.0,
        "total_qty": 60.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 5.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 5.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 14.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 14.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 12.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 12.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 4.0,
        "qty_dinner": 4.0,
        "total_qty": 8.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 43,
        "qty_breakfast": 0.0,
        "qty_lunch": 90.0,
        "qty_dinner": 0.0,
        "total_qty": 90.0,
        "unit_price_ttc": 348.8
      },
      {
        "article_id": 46,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 100.0,
        "total_qty": 100.0,
        "unit_price_ttc": 130.8
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 10.0,
        "qty_dinner": 0.0,
        "total_qty": 10.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 37,
        "qty_breakfast": 7.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 7.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 180.0,
        "qty_dinner": 0.0,
        "total_qty": 180.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 52,
        "qty_breakfast": 0.0,
        "qty_lunch": 842.0,
        "qty_dinner": 890.0,
        "total_qty": 1732.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 56,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 0.0,
        "total_qty": 30.0,
        "unit_price_ttc": 618.8
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 12.0,
        "qty_dinner": 18.0,
        "total_qty": 30.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 6.0,
        "total_qty": 12.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 885.0,
        "total_qty": 885.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 6.0,
        "qty_dinner": 6.0,
        "total_qty": 12.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 73,
        "qty_breakfast": 0.0,
        "qty_lunch": 15.0,
        "qty_dinner": 0.0,
        "total_qty": 15.0,
        "unit_price_ttc": 1142.3999999999999
      },
      {
        "article_id": 75,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 1309.0
      },
      {
        "article_id": 80,
        "qty_breakfast": 375.0,
        "qty_lunch": 840.0,
        "qty_dinner": 0.0,
        "total_qty": 1215.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 83,
        "qty_breakfast": 50.0,
        "qty_lunch": 20.0,
        "qty_dinner": 0.0,
        "total_qty": 70.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 90,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 1500.0,
        "total_qty": 1500.0,
        "unit_price_ttc": 75.8
      },
      {
        "article_id": 91,
        "qty_breakfast": 1200.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 1200.0,
        "unit_price_ttc": 46.64
      },
      {
        "article_id": 98,
        "qty_breakfast": 200.0,
        "qty_lunch": 900.0,
        "qty_dinner": 900.0,
        "total_qty": 2000.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 372,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 835,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 880,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 110409.29999999999,
    "lu_expense": 335961.5,
    "di_expense": 599576.3999999999,
    "total_expense": 1045947.2
  },
  {
    "date": "2026-10-29",
    "supply": [],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [
      {
        "article_id": 1,
        "qty_breakfast": 0.0,
        "qty_lunch": 15.0,
        "qty_dinner": 220.0,
        "total_qty": 235.0,
        "unit_price_ttc": 1595.0
      },
      {
        "article_id": 3,
        "qty_breakfast": 0.0,
        "qty_lunch": 240.0,
        "qty_dinner": 25.0,
        "total_qty": 265.0,
        "unit_price_ttc": 450.0
      },
      {
        "article_id": 4,
        "qty_breakfast": 0.0,
        "qty_lunch": 210.0,
        "qty_dinner": 0.0,
        "total_qty": 210.0,
        "unit_price_ttc": 16.0
      },
      {
        "article_id": 5,
        "qty_breakfast": 0.0,
        "qty_lunch": 38.0,
        "qty_dinner": 38.0,
        "total_qty": 76.0,
        "unit_price_ttc": 93.0
      },
      {
        "article_id": 10,
        "qty_breakfast": 0.0,
        "qty_lunch": 40.0,
        "qty_dinner": 40.0,
        "total_qty": 80.0,
        "unit_price_ttc": 75.0
      },
      {
        "article_id": 21,
        "qty_breakfast": 0.0,
        "qty_lunch": 52.0,
        "qty_dinner": 0.0,
        "total_qty": 52.0,
        "unit_price_ttc": 95.0
      },
      {
        "article_id": 23,
        "qty_breakfast": 0.0,
        "qty_lunch": 48.0,
        "qty_dinner": 25.0,
        "total_qty": 73.0,
        "unit_price_ttc": 120.0
      },
      {
        "article_id": 33,
        "qty_breakfast": 0.0,
        "qty_lunch": 42.0,
        "qty_dinner": 0.0,
        "total_qty": 42.0,
        "unit_price_ttc": 65.0
      },
      {
        "article_id": 34,
        "qty_breakfast": 3.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 3.0,
        "unit_price_ttc": 1000.0
      },
      {
        "article_id": 35,
        "qty_breakfast": 8.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 8.0,
        "unit_price_ttc": 1100.0
      },
      {
        "article_id": 36,
        "qty_breakfast": 8.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 8.0,
        "unit_price_ttc": 90.0
      },
      {
        "article_id": 39,
        "qty_breakfast": 0.0,
        "qty_lunch": 4.0,
        "qty_dinner": 4.0,
        "total_qty": 8.0,
        "unit_price_ttc": 600.0
      },
      {
        "article_id": 42,
        "qty_breakfast": 0.0,
        "qty_lunch": 25.0,
        "qty_dinner": 90.0,
        "total_qty": 115.0,
        "unit_price_ttc": 152.60000000000002
      },
      {
        "article_id": 45,
        "qty_breakfast": 0.0,
        "qty_lunch": 80.0,
        "qty_dinner": 10.0,
        "total_qty": 90.0,
        "unit_price_ttc": 403.3
      },
      {
        "article_id": 49,
        "qty_breakfast": 0.0,
        "qty_lunch": 0.0,
        "qty_dinner": 10.0,
        "total_qty": 10.0,
        "unit_price_ttc": 392.40000000000003
      },
      {
        "article_id": 37,
        "qty_breakfast": 5.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 5.0,
        "unit_price_ttc": 654.5
      },
      {
        "article_id": 50,
        "qty_breakfast": 0.0,
        "qty_lunch": 180.0,
        "qty_dinner": 180.0,
        "total_qty": 360.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 52,
        "qty_breakfast": 0.0,
        "qty_lunch": 726.0,
        "qty_dinner": 782.0,
        "total_qty": 1508.0,
        "unit_price_ttc": 17.849999999999998
      },
      {
        "article_id": 53,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 1428.0
      },
      {
        "article_id": 38,
        "qty_breakfast": 4.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 4.0,
        "unit_price_ttc": 273.7
      },
      {
        "article_id": 56,
        "qty_breakfast": 0.0,
        "qty_lunch": 30.0,
        "qty_dinner": 30.0,
        "total_qty": 60.0,
        "unit_price_ttc": 618.8
      },
      {
        "article_id": 57,
        "qty_breakfast": 0.0,
        "qty_lunch": 12.0,
        "qty_dinner": 18.0,
        "total_qty": 30.0,
        "unit_price_ttc": 357.0
      },
      {
        "article_id": 58,
        "qty_breakfast": 0.0,
        "qty_lunch": 5.0,
        "qty_dinner": 6.0,
        "total_qty": 11.0,
        "unit_price_ttc": 47.599999999999994
      },
      {
        "article_id": 67,
        "qty_breakfast": 0.0,
        "qty_lunch": 728.0,
        "qty_dinner": 0.0,
        "total_qty": 728.0,
        "unit_price_ttc": 26.18
      },
      {
        "article_id": 68,
        "qty_breakfast": 0.0,
        "qty_lunch": 2.0,
        "qty_dinner": 2.0,
        "total_qty": 4.0,
        "unit_price_ttc": 238.0
      },
      {
        "article_id": 69,
        "qty_breakfast": 0.0,
        "qty_lunch": 5.0,
        "qty_dinner": 6.0,
        "total_qty": 11.0,
        "unit_price_ttc": 119.0
      },
      {
        "article_id": 72,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 595.0
      },
      {
        "article_id": 73,
        "qty_breakfast": 0.0,
        "qty_lunch": 15.0,
        "qty_dinner": 0.0,
        "total_qty": 15.0,
        "unit_price_ttc": 1142.3999999999999
      },
      {
        "article_id": 75,
        "qty_breakfast": 0.0,
        "qty_lunch": 1.0,
        "qty_dinner": 1.0,
        "total_qty": 2.0,
        "unit_price_ttc": 1309.0
      },
      {
        "article_id": 80,
        "qty_breakfast": 185.0,
        "qty_lunch": 0.0,
        "qty_dinner": 785.0,
        "total_qty": 970.0,
        "unit_price_ttc": 23.799999999999997
      },
      {
        "article_id": 83,
        "qty_breakfast": 0.0,
        "qty_lunch": 15.0,
        "qty_dinner": 0.0,
        "total_qty": 15.0,
        "unit_price_ttc": 218.95999999999998
      },
      {
        "article_id": 92,
        "qty_breakfast": 600.0,
        "qty_lunch": 0.0,
        "qty_dinner": 0.0,
        "total_qty": 600.0,
        "unit_price_ttc": 8.5
      },
      {
        "article_id": 98,
        "qty_breakfast": 100.0,
        "qty_lunch": 800.0,
        "qty_dinner": 800.0,
        "total_qty": 1700.0,
        "unit_price_ttc": 7.5
      }
    ],
    "bf_students": 180,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 717,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 777,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 27140.3,
    "lu_expense": 302503.54000000004,
    "di_expense": 487062.3,
    "total_expense": 816706.14
  },
  {
    "date": "2026-10-30",
    "supply": [],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [],
    "bf_students": 0,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 0,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 0,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 0.0,
    "lu_expense": 0.0,
    "di_expense": 0.0,
    "total_expense": 0.0
  },
  {
    "date": "2026-10-31",
    "supply": [],
    "loan_in": [],
    "loan_out": [],
    "kitchen": [],
    "bf_students": 0,
    "bf_staff": 0,
    "bf_professors": 0,
    "bf_guests": 0,
    "bf_free": 0,
    "lu_students": 0,
    "lu_staff": 0,
    "lu_professors": 0,
    "lu_guests": 0,
    "lu_free": 0,
    "di_students": 0,
    "di_staff": 0,
    "di_professors": 0,
    "di_guests": 0,
    "di_free": 0,
    "bf_expense": 0.0,
    "lu_expense": 0.0,
    "di_expense": 0.0,
    "total_expense": 0.0
  }
]


def seed_residence_4(conn: sqlite3.Connection, force: bool = False) -> dict:
    """
    ترحيل وبذر كافة بيانات الإقامة 4 لشهر سبتمبر وأكتوبر 2026.
    متوافق مع العمليات التراكمية، ومؤمن لعدم تكرار الإدخال.
    """
    residence_id = 4
    stats = {"entries": 0, "exits": 0, "movements": 0, "meals": 0}

    cur = conn.execute("SELECT COUNT(*) FROM stock_movements WHERE residence_id = ?", (residence_id,))
    cnt = cur.fetchone()[0]
    if cnt > 0 and not force:
        logger.info(f"بيانات الإقامة 4 موجودة مسبقاً ({cnt} حركة مخزنية)، تم تجاوز البذر.")
        return stats

    logger.info("بدء بذر بيانات الإقامة الجامعية حساني محمد بن إبراهيم (residence_id=4)...")

    # 1. بذر مخزون أول مدة في residence_articles
    for aid, init_val in INITIAL_STOCKS.items():
        conn.execute("""
            INSERT INTO residence_articles (residence_id, article_id, initial_stock, current_stock, safety_stock, current_pmp)
            VALUES (?, ?, ?, ?, 10.0, 0.0)
            ON CONFLICT(residence_id, article_id) DO UPDATE SET
                initial_stock = excluded.initial_stock,
                current_stock = excluded.initial_stock
        """, (residence_id, int(aid), float(init_val), float(init_val)))

    # 2. معالجة الأيام يوماً بيوم
    for day in DAILY_DATA:
        date_str = day["date"]

        # 2.1 توريد (SUPPLY)
        if day["supply"]:
            tot_sup = sum(it["quantity"] * it["unit_price_ttc"] for it in day["supply"])
            v_num = f"BE-{residence_id}-{date_str}-SUP"
            cur = conn.execute("""
                INSERT INTO entry_vouchers (voucher_number, date, voucher_type, residence_id, delivery_note_ref, total_amount, notes)
                VALUES (?, ?, 'SUPPLIER', ?, 'AUTO-DAILY', ?, 'توريد ورقة اليوم')
            """, (v_num, date_str, residence_id, tot_sup))
            v_id = cur.lastrowid
            stats["entries"] += 1

            for it in day["supply"]:
                aid = it["article_id"]
                q = it["quantity"]
                p = it["unit_price_ttc"]
                tot_p = q * p
                conn.execute("""
                    INSERT INTO entry_voucher_items (voucher_id, article_id, quantity, unit_price_ttc, total_price)
                    VALUES (?, ?, ?, ?, ?)
                """, (v_id, aid, q, p, tot_p))
                conn.execute("""
                    INSERT INTO stock_movements (date, article_id, movement_type, voucher_id, residence_id, qty_in, qty_out, unit_price, total_value, balance_after)
                    VALUES (?, ?, 'SUPPLY_IN', ?, ?, ?, 0, ?, ?, 0)
                """, (date_str, aid, v_id, residence_id, q, p, tot_p))
                stats["movements"] += 1

        # 2.2 استعارة (LOAN_IN)
        if day["loan_in"]:
            tot_lin = sum(it["quantity"] * it["unit_price_ttc"] for it in day["loan_in"])
            v_num = f"BE-{residence_id}-{date_str}-LOAN-IN"
            cur = conn.execute("""
                INSERT INTO entry_vouchers (voucher_number, date, voucher_type, residence_id, delivery_note_ref, total_amount, notes)
                VALUES (?, ?, 'LOAN_IN', ?, 'AUTO-DAILY', ?, 'استعارة ورقة اليوم')
            """, (v_num, date_str, residence_id, tot_lin))
            v_id = cur.lastrowid
            stats["entries"] += 1

            for it in day["loan_in"]:
                aid = it["article_id"]
                q = it["quantity"]
                p = it["unit_price_ttc"]
                tot_p = q * p
                conn.execute("""
                    INSERT INTO entry_voucher_items (voucher_id, article_id, quantity, unit_price_ttc, total_price)
                    VALUES (?, ?, ?, ?, ?)
                """, (v_id, aid, q, p, tot_p))
                conn.execute("""
                    INSERT INTO stock_movements (date, article_id, movement_type, voucher_id, residence_id, qty_in, qty_out, unit_price, total_value, balance_after)
                    VALUES (?, ?, 'LOAN_IN', ?, ?, ?, 0, ?, ?, 0)
                """, (date_str, aid, v_id, residence_id, q, p, tot_p))
                stats["movements"] += 1

        # 2.3 إعارة (LOAN_OUT)
        if day["loan_out"]:
            tot_lot = sum(it["total_qty"] * it["unit_price_ttc"] for it in day["loan_out"])
            v_num = f"BS-{residence_id}-{date_str}-LOAN-OUT"
            cur = conn.execute("""
                INSERT INTO exit_vouchers (voucher_number, date, voucher_type, residence_id, destination_residence, total_amount, notes)
                VALUES (?, ?, 'LOAN_OUT', ?, 'إقامة مجاورة', ?, 'إعارة ورقة اليوم')
            """, (v_num, date_str, residence_id, tot_lot))
            v_id = cur.lastrowid
            stats["exits"] += 1

            for it in day["loan_out"]:
                aid = it["article_id"]
                q = it["total_qty"]
                p = it["unit_price_ttc"]
                tot_p = q * p
                conn.execute("""
                    INSERT INTO exit_voucher_items (voucher_id, article_id, qty_breakfast, qty_lunch, qty_dinner, qty_other, total_qty, unit_price_ttc, total_cost)
                    VALUES (?, ?, 0, 0, 0, ?, ?, ?, ?)
                """, (v_id, aid, q, q, p, tot_p))
                conn.execute("""
                    INSERT INTO stock_movements (date, article_id, movement_type, voucher_id, residence_id, qty_in, qty_out, unit_price, total_value, balance_after)
                    VALUES (?, ?, 'LOAN_OUT', ?, ?, 0, ?, ?, ?, 0)
                """, (date_str, aid, v_id, residence_id, q, p, tot_p))
                stats["movements"] += 1

        # 2.4 استهلاك المطبخ (KITCHEN)
        if day["kitchen"]:
            tot_bf = sum(it["qty_breakfast"] * it["unit_price_ttc"] for it in day["kitchen"])
            tot_lu = sum(it["qty_lunch"] * it["unit_price_ttc"] for it in day["kitchen"])
            tot_di = sum(it["qty_dinner"] * it["unit_price_ttc"] for it in day["kitchen"])
            tot_ktc = tot_bf + tot_lu + tot_di
            v_num = f"BS-{residence_id}-{date_str}-KITCHEN"

            cur = conn.execute("""
                INSERT INTO exit_vouchers (
                    voucher_number, date, voucher_type, residence_id,
                    total_breakfast_cost, total_lunch_cost, total_dinner_cost, total_amount, notes
                ) VALUES (?, ?, 'KITCHEN', ?, ?, ?, ?, ?, 'استهلاك ورقة اليوم')
            """, (v_num, date_str, residence_id, tot_bf, tot_lu, tot_di, tot_ktc))
            v_id = cur.lastrowid
            stats["exits"] += 1

            for it in day["kitchen"]:
                aid = it["article_id"]
                bf = it["qty_breakfast"]
                lu = it["qty_lunch"]
                di = it["qty_dinner"]
                tot = it["total_qty"]
                p = it["unit_price_ttc"]
                tot_p = tot * p

                conn.execute("""
                    INSERT INTO exit_voucher_items (
                        voucher_id, article_id, qty_breakfast, qty_lunch, qty_dinner, qty_other, total_qty, unit_price_ttc, total_cost
                    ) VALUES (?, ?, ?, ?, ?, 0, ?, ?, ?)
                """, (v_id, aid, bf, lu, di, tot, p, tot_p))

                if bf > 0:
                    conn.execute("""
                        INSERT INTO stock_movements (date, article_id, movement_type, voucher_id, residence_id, qty_in, qty_out, unit_price, total_value, balance_after)
                        VALUES (?, ?, 'BREAKFAST_OUT', ?, ?, 0, ?, ?, ?, 0)
                    """, (date_str, aid, v_id, residence_id, bf, p, bf * p))
                    stats["movements"] += 1
                if lu > 0:
                    conn.execute("""
                        INSERT INTO stock_movements (date, article_id, movement_type, voucher_id, residence_id, qty_in, qty_out, unit_price, total_value, balance_after)
                        VALUES (?, ?, 'LUNCH_OUT', ?, ?, 0, ?, ?, ?, 0)
                    """, (date_str, aid, v_id, residence_id, lu, p, lu * p))
                    stats["movements"] += 1
                if di > 0:
                    conn.execute("""
                        INSERT INTO stock_movements (date, article_id, movement_type, voucher_id, residence_id, qty_in, qty_out, unit_price, total_value, balance_after)
                        VALUES (?, ?, 'DINNER_OUT', ?, ?, 0, ?, ?, ?, 0)
                    """, (date_str, aid, v_id, residence_id, di, p, di * p))
                    stats["movements"] += 1

        # 2.5 تذاكر الوجبات (Daily Meals Tracking)
        bf_tot = day["bf_students"] + day["bf_staff"] + day["bf_professors"] + day["bf_guests"] + day["bf_free"]
        lu_tot = day["lu_students"] + day["lu_staff"] + day["lu_professors"] + day["lu_guests"] + day["lu_free"]
        di_tot = day["di_students"] + day["di_staff"] + day["di_professors"] + day["di_guests"] + day["di_free"]

        if di_tot == 0:
            avg_m = float(lu_tot)
        else:
            avg_m = float((lu_tot + di_tot) / 2.0)

        tot_lu_di = lu_tot + di_tot
        d_expense = day["total_expense"]
        if tot_lu_di > 0:
            cost_stud = d_expense / float(tot_lu_di)
        else:
            cost_stud = 0.0

        conn.execute("""
            INSERT INTO daily_meals_tracking (
                residence_id, date,
                bf_students, bf_staff, bf_professors, bf_guests, bf_free, bf_total,
                lu_students, lu_staff, lu_professors, lu_guests, lu_free, lu_total,
                di_students, di_staff, di_professors, di_guests, di_free, di_total,
                average_daily_meals, daily_food_expense, student_daily_cost,
                bf_expense, lu_expense, di_expense, menu_breakfast, menu_lunch, menu_dinner, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', '', '', 'مستورد من السجلات الرسمية للإقامة')
            ON CONFLICT(residence_id, date) DO UPDATE SET
                bf_students = excluded.bf_students,
                bf_staff = excluded.bf_staff,
                bf_professors = excluded.bf_professors,
                bf_guests = excluded.bf_guests,
                bf_free = excluded.bf_free,
                bf_total = excluded.bf_total,
                lu_students = excluded.lu_students,
                lu_staff = excluded.lu_staff,
                lu_professors = excluded.lu_professors,
                lu_guests = excluded.lu_guests,
                lu_free = excluded.lu_free,
                lu_total = excluded.lu_total,
                di_students = excluded.di_students,
                di_staff = excluded.di_staff,
                di_professors = excluded.di_professors,
                di_guests = excluded.di_guests,
                di_free = excluded.di_free,
                di_total = excluded.di_total,
                average_daily_meals = excluded.average_daily_meals,
                daily_food_expense = excluded.daily_food_expense,
                student_daily_cost = excluded.student_daily_cost,
                bf_expense = excluded.bf_expense,
                lu_expense = excluded.lu_expense,
                di_expense = excluded.di_expense
        """, (
            residence_id, date_str,
            day["bf_students"], day["bf_staff"], day["bf_professors"], day["bf_guests"], day["bf_free"], bf_tot,
            day["lu_students"], day["lu_staff"], day["lu_professors"], day["lu_guests"], day["lu_free"], lu_tot,
            day["di_students"], day["di_staff"], day["di_professors"], day["di_guests"], day["di_free"], di_tot,
            avg_m, d_expense, cost_stud,
            day["bf_expense"], day["lu_expense"], day["di_expense"]
        ))
        stats["meals"] += 1

    # 3. تحديث الأرصدة الحالية في residence_articles للإقامة 4 فقط
    inits_map = {
        r["article_id"]: r["initial_stock"]
        for r in conn.execute("SELECT article_id, initial_stock FROM residence_articles WHERE residence_id = ?", (residence_id,)).fetchall()
    }
    moves_map = {
        r["article_id"]: (r["tot_in"], r["tot_out"])
        for r in conn.execute("""
            SELECT article_id, COALESCE(SUM(qty_in), 0) as tot_in, COALESCE(SUM(qty_out), 0) as tot_out
            FROM stock_movements WHERE residence_id = ? GROUP BY article_id
        """, (residence_id,)).fetchall()
    }

    all_arts = conn.execute("SELECT id, price_ttc FROM articles WHERE is_active = 1").fetchall()
    batch_updates = []
    for a in all_arts:
        aid = a["id"]
        init_stk = inits_map.get(aid, 0.0)
        tot_in, tot_out = moves_map.get(aid, (0.0, 0.0))
        cur_stk = init_stk + tot_in - tot_out
        batch_updates.append((residence_id, aid, init_stk, cur_stk, 10.0, a["price_ttc"]))

    conn.executemany("""
        INSERT INTO residence_articles (residence_id, article_id, initial_stock, current_stock, safety_stock, current_pmp)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(residence_id, article_id) DO UPDATE SET
            initial_stock = excluded.initial_stock,
            current_stock = excluded.current_stock
    """, batch_updates)

    conn.commit()
    logger.info(f"تم اكتمال بذر بيانات الإقامة 4 بنجاح! الإحصائيات: {stats}")
    return stats
