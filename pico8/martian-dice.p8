pico-8 cartridge // http://www.pico-8.com
version 32
__lua__
local_run=false

phase={
 throwing=1,
 thrown=2,
 movedtanks=3,
 pickdice=4,
 pickeddice=5,
 checkpass=6,
 done=7
}

endcause={
 [1]="cannot improve score",
 [2]="player choice",
 [3]="no more dice",
 [4]="cannot select a die",
 [5]="defeated!",
 [6]="turn forcefully ended"
}

function shuffle(l)
 for i=1,#l do
  local j=flr(rnd(#l-i+1))+i
  if i!=j then
   local tmp=l[i]
   l[i]=l[j]
   l[j]=tmp
  end
 end
 return l
end

function print_outlined(
 msg,x,y,col
)
 color(1)
 print(msg,x-1,y)
 print(msg,x+1,y)
 print(msg,x,y-1)
 print(msg,x,y+1)

 color(0)
 print(msg,x+1,y+1)

 color(11)
 print(msg,x,y)
end

function draw_throw(throw)
 for i=1,#throw do
  if throw[i]>0 then
   local x=((i-1)%7)*16+8
   local y=flr((i-1)/7)*16+8
   spr(2+2*throw[i],x,y,2,2)
  end
 end
end

function draw_battle(battle)
 for i=1,#battle do
  for j=1,battle[i] do
   spr(2+i*2,j*16-8,32+i*16,2,2)
  end
 end
end

function draw_collected(collected)
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

function title_draw()
 cls(0)
 spr(128,32,40,9,4)
 print("v0.1")
 
 if peek(a_room)==1 then
  print("joining room...",36,80,3)
 end
end

function game_draw()
 cls(0)
 
 if game==nil then
  return
 end

 color(3)
 print("round "..game.round,0,0)
 print("player #"..game.turn,46,0)
 print("throw "..game.thrownum,100,0)

 draw_throw(game.throw)
 draw_battle(game.battle)
 draw_collected(game.collected)

 if game.endcause!=0 then
  local msg=endcause[game.endcause]
  print_outlined(
   msg,64-2*#msg,15
  )
  
  msg="+"..game.scored.." => "
  msg=msg..game.score.."(#"
  msg=msg..game.position..")"
  print_outlined(
   msg,64-2*#msg,26
  )
 end
end

function room_draw()
 game_draw()
end

-->8
--0:ready for write
--1:ready for read
a_ctrl_in_game=0x5f80
a_ctrl_in_room=0x5f81
a_ctrl_out=0x5f82
a_ctrl_dump=0x5f83

--0:none
--1:initiate join (set by p8)
--2:initiating join
--3:joined
--4:initiate exit (set by p8)
a_room=0x5f88

a_thrw=0x5f90 -- 5 bytes
a_side=0x5f95 -- 5 bytes

--scoring
a_endc=0x5f9a --end cause
a_trsc=0x5f9b --turn score
a_ttsc=0x5f9c --tot. score
a_cpos=0x5f9d --cur. position

--round/turn/throw/phase counters
a_crou=0x5fa0
a_ctur=a_crou+1
a_cthr=a_ctur+1
a_cpha=a_cthr+1

function pop_gpio()
 poke(a_thrw,1)
 poke(a_thrw+1,2)
 poke(a_thrw+2,3)
 poke(a_thrw+3,4)
 poke(a_thrw+4,3)

 poke(a_side,4)
 poke(a_side+1,3)
 poke(a_side+2,3)
 poke(a_side+3,2)
 poke(a_side+4,1)

 poke(a_crou,3)
 poke(a_ctur,1)
 poke(a_cthr,2)
 poke(a_cpha,2)
 
 poke(a_endc,1)
 poke(a_trsc,3)
 poke(a_ttsc,8)
 poke(a_cpos,2)

 poke(a_ctrl_in_game,1)
end

function start_game()
 --ready for write
 if not local_run then
  poke(a_ctrl_in_game,0)
 end

 game=nil
 game_gpio_read_delay=0
end

function new_collected(dice)
 local l={}

 for tp,num in pairs(dice) do
  add(l,{tp,num})
 end

 return l 
end

--updates collected while
--preserving order.
--old is list, new is dict.
function update_collected(
 old,new
)
 local l={}

 for tuple in all(old) do
  local tp=tuple[1]
  if new[tp]>0 then
   add(l,{tp,new[tp]})
   new[tp]=0
  end
 end

 for tp,num in pairs(new) do
  if num>0 then
   add(l,{tp,num})
  end
 end

 return l
end

function new_throw(dice)
 local l={}
 for tp,num in pairs(dice) do
  for i=1,num do
   add(l,tp)
  end
 end

 return shuffle(l)
end

--old is list, new is dict
function update_throw(old,new)
 local l={}
 for tp in all(old) do
  if tp!=0 and new[tp]>0 then
   add(l,tp)
   new[tp]-=1
  else
   add(l,0)
  end
 end

 --just in case, add new dice
 local i=1
 for tp,num in pairs(new) do
  while num>0 do
   while l[i]!=0 and i<13 do
    i+=1
   end
   l[i]=tp
   num-=1
  end
 end

 return l
end

game_gpio_read_delay=0
function read_gpio_game()
 if peek(a_ctrl_in_game)!=1 then
  return
 end
 if game_gpio_read_delay>0 then
  game_gpio_read_delay-=1
  return
 end
 
 local g={}
 g.round=peek(a_crou)
 g.turn=peek(a_ctur)
 g.thrownum=peek(a_cthr)
 g.phase=peek(a_cpha)

 g.endcause=peek(a_endc)
 g.scored=peek(a_trsc)
 g.score=peek(a_ttsc)
 g.position=peek(a_cpos)

 local dice={}
 for i=1,5 do
  dice[i]=peek(a_thrw+i-1)
 end
 if (
  g.phase==phase.thrown or
  game==nil
 ) then
  g.throw=new_throw(dice)
 else
  g.throw=update_throw(
   game.throw,dice
  )
 end

 g.battle={}
 add(g.battle,peek(a_side))
 add(g.battle,peek(a_side+1))

 dice={}
 for i=3,5 do
  dice[i]=peek(a_side+i-1)
 end
 if game==nil then
  g.collected=new_collected(dice)
 else
  g.collected=update_collected(
   game.collected,dice
  )
 end

 game=g 
 game_gpio_read_delay=60
 poke(a_ctrl_in_game,0)
end

function read_gpio()
 read_gpio_game()
 --todo: read_gpio_room()
end

function room_update()
 if peek(a_room)==0 then
  --exited room
  _update=title_update
  _draw=title_draw
 end

 if btnp(4) then
  if peek(a_room)==3 then
   --initiate room exit
   poke(a_room,4)
  end
 end

 read_gpio()

 --tmp:debug 
 if btnp(5) then
  poke(a_ctrl_dump,1)
 end
end

function title_update()
 if peek(a_room)==3 then
  --entered room
  _update=room_update
  _draw=room_draw

  start_game()
 end

 if btnp(4) or btnp(5) then
  if peek(a_room)==0 then
   --initiate room entry
   poke(a_room,1)
  end
 end

 --tmp:debug 
 if btnp(5) then
  poke(a_ctrl_dump,1)
 end
end

_draw=title_draw
_update=title_update
-->8
function _init()
 if local_run then
  pop_gpio()
  poke(a_room,3)
  --refresh_count=60
 else
  poke(a_room,0)
 end
end

__gfx__
00000000bbbbbbb00000000007777770011111111111110001111111111111000111111111111100011111111111110001111111111111000000000000000000
00000000b00000b00000008077777777111111111111111011111111111111101111111aa1111110111111111111111011111111111111100000000000000000
00700700b0bbb0b0888888887707707711111111111111101111111111111110111111a11a111110117771777177711011111ccccc1111100000000000000000
00077000b0bbb0b0088000807777777711111111111111101111111111111110111aa1aaaa1aa11011711711171171101111c11111c111100000000000000000
00077000b0bbb0b00880000077777777111111bbb1111110111111888118811011a11a1111a11a101117711111771110111c1111111c11100000000000000000
007007000b0b0b00880000007707707711111b111b111110111118111881111011a1a111111a1a10111171717171111011c11c111c11c1100000000000000000
000000000bb0bb00880000007777777711111b111b1111101111188888111110111a11111111a110111171717171111011c11c111c11c1100000000000000000
0000000000bbb000000000000777777011bbbbbbbbbbb1101188888888888110111a1a111111a110111171111171111011c111111111c1100000000000000000
0000000000cccc00aa00a0aa000000001b11111111111b10181111111111181011aa11111111a110111177777771111011c1c11111c1c1100000000000000000
000000000cccccc0aaaa00aa000000001b11111111111b1018181111111818101aaa11111111a110111711111117111011c11c111c11c1100000000000000000
00000000cc0cc0cc00000a00000000001b11111111111b1018111111111118101111a111111a11101171117171117110111c11ccc11c11100000000000000000
00000000cc0cc0cc00a0a00a0000000011bbbbbbbbbbb110118888888888811011111a1111a1111011711111111171101111c11111c111100000000000000000
00000000cccccccc00a0a0a00000000011111111111111101111111111111110111111aaaa111110111711111117111011111ccccc1111100000000000000000
00000000cc0cc0cc00a0a0a000000000111111111111111011111111111111101111111111111110111177777771111011111111111111100000000000000000
000000000cc00cc0aa00a0aa00000000011111111111110001111111111111000111111111111100011111111111110001111111111111000000000000000000
0000000000cccc00aa00a0aa00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
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
00030000000300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00033000003300000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00033300033300000000000000000000000000000033000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00333333333330000000300000000000000000000033000000300000030000030000000000000000000000000000000000000000000000000000000000000000
00330333330330000000300000000000000000000000000000300000030000030000000000000000000000000000000000000000000000000000000000000000
00330333330330000003330033333330033333333333300003330000033000330000000000000000000000000000000000000000000000000000000000000000
00330033300330000003330000333333000333333000000003330000033000330000000000000000000000000000000000000000000000000000000000000000
00330033300333000003030000033003300003300033000003030000033300330000000000000000000000000000000000000000000000000000000000000000
03330003000333000033033000033003300003300033000033033000033300330000000000000000000000000000000000000000000000000000000000000000
03330003000333000030003000033003300003300033000030003000033330330000000000000000000000000000000000000000000000000000000000000000
03330003000333000330003300033333000003300033000330003300033030330000000000000000000000000000000000000000000000000000000000000000
03330003000333000333333300033333000003300033000333333300033033330000000000000000000000000000000000000000000000000000000000000000
03330000000333000330003300033003000003300033000330003300033003330000000000000000000000000000000000000000000000000000000000000000
03330000000333000330003300033003300003300033000330003300033003330000000000000000000000000000000000000000000000000000000000000000
03330000000333000330003300033003300033330333300330003300033000330000000000000000000000000000000000000000000000000000000000000000
33333000003333303330003330333003330033330333303330003330333000333000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000003333330033330033333300333333000000000000000000000000000000000000000000000000000000000000000000000000000000000
0000000bbb00000000000333330033003333300033333000000000bbb00000000000000000000000000000000000000000000000000000000000000000000000
000000b000b000000033000033303303330000033300000000000b000b0000000000000000000000000000000000000000000000000000000000000000000000
000000b000b000000003300003303303300000033000000000000b000b0000000000000000000000000000000000000000000000000000000000000000000000
000bbbbbbbbbbb000003300003303303300000033330000000bbbbbbbbbbb0000000000000000000000000000000000000000000000000000000000000000000
00b00000000000b0000330000330330330000003333330000b00000000000b000000000000000000000000000000000000000000000000000000000000000000
00b00000000000b0000330000330330330000003333000000b00000000000b000000000000000000000000000000000000000000000000000000000000000000
00b00000000000b0000330000330330330000003300000000b00000000000b000000000000000000000000000000000000000000000000000000000000000000
000bbbbbbbbbbb000033000033303303330000033300000000bbbbbbbbbbb0000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000033333003300333330003333300000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000003333330033330033333300333333000000000000000000000000000000000000000000000000000000000000000000000000000000000
__label__
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
00000000000000000000000000000000000300000003000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000330000033000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000333000333000000000000000000000000000000330000000000000000000000000000000000000000000000000000
00000000000000000000000000000000003333333333300000003000000000000000000000330000003000000300000300000000000000000000000000000000
00000000000000000000000000000000003303333303300000003000000000000000000000000000003000000300000300000000000000000000000000000000
00000000000000000000000000000000003303333303300000033300333333300333333333333000033300000330003300000000000000000000000000000000
00000000000000000000000000000000003300333003300000033300003333330003333330000000033300000330003300000000000000000000000000000000
00000000000000000000000000000000003300333003330000030300000330033000033000330000030300000333003300000000000000000000000000000000
00000000000000000000000000000000033300030003330000330330000330033000033000330000330330000333003300000000000000000000000000000000
00000000000000000000000000000000033300030003330000300030000330033000033000330000300030000333303300000000000000000000000000000000
00000000000000000000000000000000033300030003330003300033000333330000033000330003300033000330303300000000000000000000000000000000
00000000000000000000000000000000033300030003330003333333000333330000033000330003333333000330333300000000000000000000000000000000
00000000000000000000000000000000033300000003330003300033000330030000033000330003300033000330033300000000000000000000000000000000
00000000000000000000000000000000033300000003330003300033000330033000033000330003300033000330033300000000000000000000000000000000
00000000000000000000000000000000033300000003330003300033000330033000333303333003300033000330003300000000000000000000000000000000
00000000000000000000000000000000333330000033333033300033303330033300333303333033300033303330003330000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000033333300333300333333003333330000000000000000000000000000000000000000000000000
000000000000000000000000000000000000000bbb00000000000333330033003333300033333000000000bbb000000000000000000000000000000000000000
00000000000000000000000000000000000000b000b000000033000033303303330000033300000000000b000b00000000000000000000000000000000000000
00000000000000000000000000000000000000b000b000000003300003303303300000033000000000000b000b00000000000000000000000000000000000000
00000000000000000000000000000000000bbbbbbbbbbb000003300003303303300000033330000000bbbbbbbbbbb00000000000000000000000000000000000
0000000000000000000000000000000000b00000000000b0000330000330330330000003333330000b00000000000b0000000000000000000000000000000000
0000000000000000000000000000000000b00000000000b0000330000330330330000003333000000b00000000000b0000000000000000000000000000000000
0000000000000000000000000000000000b00000000000b0000330000330330330000003300000000b00000000000b0000000000000000000000000000000000
00000000000000000000000000000000000bbbbbbbbbbb000033000033303303330000033300000000bbbbbbbbbbb00000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000333330033003333300033333000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000033333300333300333333003333330000000000000000000000000000000000000000000000000
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
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000

__map__
00000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000
