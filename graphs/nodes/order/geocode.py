import geocoder


def geocode_order(state):

    order = state.incoming_order

    pickup = geocoder.osm(order.pickup_address)
    delivery = geocoder.osm(order.delivery_address)

    if not pickup.ok:
        state.valid = False
        state.validation_errors.append(
            f"Unable to geocode pickup address: {order.pickup_address}"
        )
        return state

    if not delivery.ok:
        state.valid = False
        state.validation_errors.append(
            f"Unable to geocode delivery address: {order.delivery_address}"
        )
        return state

    order.pickup_lat = pickup.lat
    order.pickup_lon = pickup.lng

    order.delivery_lat = delivery.lat
    order.delivery_lon = delivery.lng

    return state