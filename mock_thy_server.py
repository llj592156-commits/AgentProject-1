from fastmcp import FastMCP

# Create an MCP server named "TurkishAirlines"
mcp = FastMCP("TurkishAirlines")

@mcp.tool()
def search_flights(origin: str, destination: str, date: str) -> str:
    """
    Search for Turkish Airlines flights between cities on specific dates.
    :param origin: IATA code or city name of origin (e.g., IST)
    :param destination: IATA code or city name of destination (e.g., JFK)
    :param date: Departure date in YYYY-MM-DD format
    """
    # Mock flight data
    flights = [
        {
            "flight_id": "TK1903",
            "origin": origin,
            "destination": destination,
            "departure": f"{date} 08:30",
            "arrival": f"{date} 11:45",
            "price": "450 EUR",
            "status": "Available"
        },
        {
            "flight_id": "TK2024",
            "origin": origin,
            "destination": destination,
            "departure": f"{date} 14:15",
            "arrival": f"{date} 17:30",
            "price": "380 EUR",
            "status": "Available"
        }
    ]
    
    result = f"Found {len(flights)} flights from {origin} to {destination} on {date}:\n"
    for f in flights:
        result += f"- {f['flight_id']}: {f['departure']} -> {f['arrival']} ({f['price']})\n"
    
    return result

@mcp.tool()
def get_miles_balance(account_id: str) -> str:
    """
    Get the Miles&Smiles balance for a member account.
    :param account_id: The Miles&Smiles account number (9 digits)
    """
    # Mock miles balance
    balance = 45200
    return f"Account {account_id} currently has {balance} Miles&Smiles miles."

@mcp.tool()
def book_flight(flight_id: str, passenger_name: str) -> str:
    """
    Book a specific flight for a passenger.
    :param flight_id: The unique ID of the flight to book
    :param passenger_name: Full name of the passenger
    """
    # Mock booking confirmation
    return f"Successfully booked flight {flight_id} for {passenger_name}. Confirmation number: THY-{flight_id}-OK"

if __name__ == "__main__":
    # Run the server using stdio transport
    mcp.run(transport="stdio")
