ss = []
original = "abcdefghijklmnopqrstuvwxyz"
original_list = list(original)


def caesarCipher(s, k):
    # Write your code here
    for i in s:
        if i in original_list and i.islower():
            ss.append(original_list[(original_list.index(i)+k) % 26])
        elif i.lower() in original_list and i.isupper():
            s = (original_list[(original_list.index(i.lower())+k) % 26])
            ss.append(s.upper())
        else:
            ss.append(i)
    return "".join(ss)


print(caesarCipher("Rando-Mstring", 3))
