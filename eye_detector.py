from math import hypot

LEFT_EYE = [33, 160, 158, 133, 153, 144]
RIGHT_EYE = [362, 385, 387, 263, 373, 380]


def distance(p1, p2):
    return hypot(p1[0] - p2[0], p1[1] - p2[1])


def get_point(landmarks, index, w, h):
    lm = landmarks.landmark[index]
    return (int(lm.x * w), int(lm.y * h))


def calculate_ear(eye_points):
    horizontal = distance(eye_points[0], eye_points[3])

    vertical1 = distance(eye_points[1], eye_points[5])
    vertical2 = distance(eye_points[2], eye_points[4])

    ear = (vertical1 + vertical2) / (2 * horizontal)

    return ear


def get_average_ear(face_landmarks, w, h):

    left_points = [
        get_point(face_landmarks, idx, w, h)
        for idx in LEFT_EYE
    ]

    right_points = [
        get_point(face_landmarks, idx, w, h)
        for idx in RIGHT_EYE
    ]

    left_ear = calculate_ear(left_points)
    right_ear = calculate_ear(right_points)

    avg_ear = (left_ear + right_ear) / 2

    return avg_ear, left_points, right_points