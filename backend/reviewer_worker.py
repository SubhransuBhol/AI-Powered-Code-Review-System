from review_engine import review_single_file


def review_file(file_data):

    filename = file_data["filename"]

    content = file_data["content"]

    review = review_single_file(
        filename,
        content
    )


    return filename, review