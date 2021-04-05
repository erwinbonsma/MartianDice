pico-8 cartridge // http://www.pico-8.com
version 23
__lua__
cls(0)

function draw_throw()
 for i=1,#throw do
  if throw[i]>0 then
   local x=((i-1)%7)*16+8
   local y=flr((i-1)/7)*16+8
   spr(2+2*throw[i],x,y,2,2)
  end
 end
end

function draw_battlezone()
 for i=1,#battle do
  for j=1,battle[i] do
   spr(2+i*2,j*16-8,32+i*16,2,2)
  end
 end
end

function draw_collected()
 local n=0
 for p in all(collected) do
  local typ=p[1]
  local num=p[2]
  for i=1,num do
   local x=(n%7)*16+8
   local y=flr(n/7)*16+88
   spr(2+typ*2,x,y,2,2)
   n+=1
  end
 end
end

function _draw()
 cls()
 palt(0,false)
 palt(1,true)
 pal(0,1)
 draw_throw()
 draw_battlezone()
 draw_collected()
 print("turn 1    player-one    throw 3")
end

-->8
--0:ready for write
--1:ready for read
a_ctrl_in_game=0x5f80
a_ctrl_in_room=0x5f81
a_ctrl_out=0x5f82

a_thrw=0x5f83 -- 13 bytes
a_side=0x5f90 --  5 bytes

function pop_gpio()
 local l={5,4,3,2,1,0,5,4,3,2,1}
 for i=1,#l do
  poke(a_thrw+i-1,l[i])
 end
 poke(a_side,4)
 poke(a_side+1,3)
 poke(a_side+2,3)
 poke(a_side+3,2)
 poke(a_side+4,1)
 poke(a_ctrl_in_game,0)
end

--updates collected while
--preserving order
function update_collected(cnew)
 local ordered={}

 for old in all(collected) do
  local tp=old[1]
  if cnew[tp]>0 then
   add(ordered,{tp,cnew[tp]})
   cnew[tp]=0
  end
 end

 for tp,num in pairs(cnew) do
  if num>0 then
   add(ordered,{tp,num})
  end
 end

 collected=ordered
end

function read_gpio()
 if peek(a_ctrl_in_game)!=1 then
  return
 end
 throw={}
 for i=0,12 do
  add(throw,peek(a_thrw+i))
 end
 battle={}
 add(battle,peek(a_side))
 add(battle,peek(a_side+1))
 local col_new={}
 for i=3,5 do
  col_new[i]=peek(a_side+i-1)
 end
 update_collected(col_new)
end

function _update()
 read_gpio()
 if refresh_count>0 then
  refresh_count-=1
  if refresh_count==0 then
   poke(a_ctrl_in_game,1)
  end
 end
end
-->8
function _init()
 throw={1,0,1,2,0,2,3,3,4,4,5,5}
 battle={2,8}
 collected={{4,2},{5,1}}

 pop_gpio()
 refresh_count=60
end

__gfx__
00000000bbbbbbb00000000007777770100000000000001110000000000000111000000000000011100000000000001110000000000000110000000000000000
00000000b00000b0000000807777777700000000000000010000000000000001000000000000000100000000000000010000000aa00000010000000000000000
00700700b0bbb0b0888888887707707700000000000000010000000000000001007770777077700100000ccccc000001000000a00a0000010000000000000000
00077000b0bbb0b008800080777777770000000000000001000000000000000100700700070070010000c00000c00001000aa0aaaa0aa0010000000000000000
00077000b0bbb0b00880000077777777000000bbb000000100000088800880010007700000770001000c0000000c000100a00a0000a00a010000000000000000
007007000b0b0b00880000007707707700000b000b0000010000080008800001000070707070000100c00c000c00c00100a0a000000a0a010000000000000000
000000000bb0bb00880000007777777700000b000b0000010000088888000001000070707070000100c00c000c00c001000a00000000a0010000000000000000
0000000000bbb000000000000777777000bbbbbbbbbbb0010088888888888001000070000070000100c000000000c001000a0a000000a0010000000000000000
0000000000cccc00aa00a0aa000000000b00000000000b010800000000000801000077777770000100c0c00000c0c00100aa00000000a0010000000000000000
000000000cccccc0aaaa00aa000000000b00000000000b010808000000080801000700000007000100c00c000c00c0010aaa00000000a0010000000000000000
00000000cc0cc0cc00000a00000000000b00000000000b0108000000000008010070007070007001000c00ccc00c00010000a000000a00010000000000000000
00000000cc0cc0cc00a0a00a0000000000bbbbbbbbbbb001008888888888800100700000000070010000c00000c0000100000a0000a000010000000000000000
00000000cccccccc00a0a0a00000000000000000000000010000000000000001000700000007000100000ccccc000001000000aaaa0000010000000000000000
00000000cc0cc0cc00a0a0a000000000000000000000000100000000000000010000777777700001000000000000000100000000000000010000000000000000
000000000cc00cc0aa00a0aa00000000100000000000001110000000000000111000000000000011100000000000001110000000000000110000000000000000
0000000000cccc00aa00a0aa00000000111111111111111111111111111111111111111111111111111111111111111111111111111111110000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00bbbbbbbbbbbbb00000000000000000007777777777700000000cccccc000000000000aa0000000000000000000000000000000000000000000000000000000
00bbbbbbbbbbbbb000000000000080800777777777777700000cccccccccc0000aaaa00aa00aaaa0000000000000000000000000000000000000000000000000
00bb000000000bb00888888888888888770007777700077000cccccccccccc000aaaaaaaa00aaaa0000000000000000000000000000000000000000000000000
00bb0bbb0bbb0bb0088888888888888877000777770007700cccccccccccccc00aaaaaaa000aaaa0000000000000000000000000000000000000000000000000
00bb0bbb0bbb0bb0088888888888888877000777770007700ccc00cccc00ccc00aaaa00000aaaaa0000000000000000000000000000000000000000000000000
00bb0bbb0bbb0bb000888800800080807777777777777770cccc00cccc00cccc000000000aaa0000000000000000000000000000000000000000000000000000
00bb0bbb0bbb0bb000888800800000007777770007777770cccccccccccccccc00000000aaa00000000000000000000000000000000000000000000000000000
00bb0bbb0bbb0bb000888800800000007777770007777770ccccccccccccccccaaa0000aaa000aaa000000000000000000000000000000000000000000000000
00bb0bbb0bbb0bb008888888000000007777770007777770ccccccccccccccccaaaa000aa000aaaa000000000000000000000000000000000000000000000000
000bb0bb0bb0bb0008888000000000007777777777777770cc0cccccccccc0cc00aa000aa000aa00000000000000000000000000000000000000000000000000
000bb0bb0bb0bb0008888000000000007700077777000770cc00cccccccc00cc00aa000aa000aa00000000000000000000000000000000000000000000000000
000bbb0b0b0bbb00888800000000000077000777770007700cc00cccccc00cc00aaaa00aa00aaaa0000000000000000000000000000000000000000000000000
0000bbb000bbb000888800000000000077000777770007700ccc00000000ccc00aaaa00aa00aaaa0000000000000000000000000000000000000000000000000
00000bbb0bbb00008888000000000000077777777777770000ccc000000ccc000aaaa00aa00aaaa0000000000000000000000000000000000000000000000000
000000bbbbb0000000000000000000000077777777777000000cccccccccc0000aaaa00aa00aaaa0000000000000000000000000000000000000000000000000
0000000bbb0000000000000000000000000000000000000000000cccccc000000000000aa0000000000000000000000000000000000000000000000000000000
