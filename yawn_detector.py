from math import hypot

MOUTH_POINTS = [61, 13, 14, 291]


def distance(p1, p2):
    return hypot(p1[0] - p2[0], p1[1] - p2[1])


def get_point(landmarks, index, w, h):
    lm = landmarks.landmark[index]
    return (int(lm.x * w), int(lm.y * h))


def calculate_mar(face_landmarks, w, h):

    points = [
        get_point(face_landmarks, idx, w, h)
        for idx in MOUTH_POINTS
    ]

    left = points[0]
    top = points[1]
    bottom = points[2]
    right = points[3]

    mouth_width = distance(left, right)
    mouth_height = distance(top, bottom)

    mar = mouth_height / mouth_width

    return mar, points