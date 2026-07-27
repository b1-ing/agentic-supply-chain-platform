from services.geocoding_service import GeocodingService


def geocode_order(state):

    order = state.order
    gcd = GeocodingService()

    pickup = gcd.geocode(order.pickup_address)
    delivery = gcd.geocode(order.delivery_address)

    print(pickup)

    if not pickup:
        state.valid = False
        state.validation_errors.append(
            f"Unable to geocode pickup address: {order.pickup_address}"
        )
        return state

    if not delivery:
        state.valid = False
        state.validation_errors.append(
            f"Unable to geocode delivery address: {order.delivery_address}"
        )
        return state

    order.pickup_lat = pickup[0]
    order.pickup_lon = pickup[1]

    order.delivery_lat = delivery[0]
    order.delivery_lon = delivery[1]

    return state
