# Polish Postal Code API

A multi-technology performance comparison framework for Polish postal code lookups.

## What it does

**Maps address to postal codes**
`Warszawa, Abramowskiego 5` → `02-659`

**Polish character support**
`Łódź` ≡ `Lodz` (both work)

**Works for every address**
Works with postal codes on different levels of granulaty.
Some postal codes are defined for cities, other for streets and in big cities buildings have own postal codes.

This API handles it all.

## Technologies

Four identical implementations for performance comparison:

| Tech     | Port | Start command |
|----------|------|---------------|
| Flask    | 5001 | `cd flask && python app.py` |
| FastAPI  | 5002 | `cd fastapi && python main.py` |
| Go       | 5003 | `cd go && ./postal-api` |
| Elixir   | 5004 | `cd elixir && mix run --no-halt` |

## Quick start

```bash
# Setup
python create_db.py
poetry install

# Run any implementation
cd flask && python app.py

# Test
curl "localhost:5001/postal-codes?city=Warszawa&street=Abramowskiego&house_number=5"
```

## API

```
GET /postal-codes?city={city}&street={street}&house_number={number}
GET /postal-codes/{code}
GET /locations/cities?prefix={text} 
GET /locations/streets?city={city}&prefix={text}
```

## Testing

```bash
# Test all implementations
python comprehensive_postal_test_suite.py

# Test specific
python comprehensive_postal_test_suite.py --api flask
python comprehensive_postal_test_suite.py --core-tests
```

---

Built to solve real address lookup challenges while comparing tech performance.