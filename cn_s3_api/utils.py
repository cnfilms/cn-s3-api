def parse_list(objects):
    list_objects = []

    for _object in objects:
        list_objects.append(dict(
            name=_object['Key'],
            datestamp=_object['LastModified'].strftime('%Y-%m-%d %H:%M'),
            byte_str=_object['Size']
        ))

    return list_objects
