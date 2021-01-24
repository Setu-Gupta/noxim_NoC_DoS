src_id, dst_id = map(int, input().split())

src = (src_id%8, src_id//8)
dst = (dst_id%8, dst_id//8)

dist = abs(src[0]-dst[0]) + abs(src[1]-dst[1])
time = 10 * dist
# start_time = int(input())
start_time = 1025

print(start_time + time)