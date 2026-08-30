const  wi = {
    name: "mission1",
    missionName: "第一关",
    nextMission: "mission2",
    bgm: {
      雨: .3,
      风: .5
    },
    mask: [{
      type: "foreground",
      background: "#000000",
      alpha: .5,
      showClue: ["-#油灯"]
    }],
    nodes: [{
      point: "center",
      name: "黑暗",
      desc: "周围一片黑暗，需要光源才能看清周围。",
      state: [{
        name: "破屋",
        preClue: ["#油灯"]
      }],
      nodes: [{
        name: "地板",
        desc: "好像有什么东西散落在地上",
        nodes: [{
          name: "火柴",
          interact: [{
            type: "use",
            target: "未点燃的油灯",
            clue: "#油灯",
            audio: "火柴点火",
            params: {
              isOnce: !0
            }
          }]
        }]
      }, {
        name: "衣柜",
        preClue: "#油灯",
        nodes: [{
          name: "密码箱",
          tip: "根据画作描绘的颜色和对应数字解出密码",
          audio: "打开衣柜",
          data: {
            lockClue: "#密码箱"
          },
          nodes: [{
            name: "0",
            type: "password",
            data: {
              color: "#362FD9",
              clue: "#blue-{0}"
            }
          }, {
            name: "0",
            type: "password",
            data: {
              color: "#E90064",
              clue: "#red-{0}"
            }
          }, {
            name: "0",
            type: "password",
            data: {
              color: "#609966",
              clue: "#green-{0}"
            }
          }, {
            name: "钥匙",
            preClue: ["#blue-2", "#red-7", "#green-4"],
            audio: "打开铁门",
            interact: [{
              type: "use",
              target: "锁着的门",
              clue: "#开门",
              audio: "门-开锁",
              params: {
                isOnce: !0
              }
            }]
          }],
          interact: [{
            type: "click",
            clue: "#密码箱",
            preClue: ["#blue-2", "#red-7", "#green-4"]
          }]
        }]
      }, {
        name: "漆黑的墙",
        desc: "墙上一片漆黑，无法看清",
        state: [{
          name: "墙",
          desc: "墙上似乎挂着几幅画作",
          preClue: ["#油灯"]
        }],
        nodes: [{
          name: "画作",
          desc: "一片蔚蓝色的天空，画作上刻着 「2」",
          preClue: "#油灯"
        }, {
          name: "画作",
          desc: "一座正在喷发的火山，画作上刻着 「7」",
          preClue: "#油灯"
        }, {
          name: "画作",
          desc: "一望无际的草原，画作上刻着 「4」",
          preClue: "#油灯"
        }]
      }, {
        name: "锁着的门",
        desc: "门上有一把锁，你需要钥匙才能打开",
        preClue: "#油灯",
        data: {
          lockClue: "#开门"
        },
        state: [{
          name: "出口",
          desc: "门已经打开，你可以出去了",
          preClue: ["#开门"]
        }],
        interact: [{
          type: "click",
          clue: "@通关",
          preClue: "#开门"
        }]
      }, {
        name: "未点燃的油灯",
        desc: "油灯可以照亮周围的情况",
        state: [{
          name: "油灯",
          desc: "油灯已经点亮了，可以照亮周围的情况",
          preClue: ["#油灯"]
        }]
      }]
    }]
  }
  , Di = {
    name: "mission2",
    missionName: "第二关",
    nextMission: "mission3",
    bgm: {
      风: .2
    },
    nodes: [{
      point: "center",
      name: "房间",
      desc: "一个破破烂烂的房间",
      nodes: [{
        name: "镣铐",
        desc: "你被镣铐锁住了",
        state: [{
          name: "解开的镣铐",
          preClue: ["#钥匙>镣铐"]
        }]
      }, {
        name: "墙上的钥匙",
        desc: "墙上悬挂着钥匙，需要一根棍子才能勾到",
        tip: "需要前置锯子加排水管拿到棍子",
        state: [{
          name: "钥匙",
          preClue: ["#棍子>墙上的钥匙"]
        }],
        interact: [{
          type: "use",
          target: "镣铐",
          clue: "#钥匙>镣铐",
          audio: "解锁1",
          preClue: ["#棍子>墙上的钥匙"],
          params: {
            isOnce: !0
          }
        }]
      }, {
        name: "柜子",
        nodes: [{
          name: "工具箱",
          audio: "打开衣柜",
          nodes: [{
            name: "转盘锁",
            tip: "根据时钟的三点半，将旋钮转至 90° 和 180°",
            data: {
              noRefreshData: !0,
              lockClue: "#转盘锁"
            },
            nodes: [{
              name: "旋钮",
              type: "angle",
              data: {
                clue: "#angle-{0}",
                precision: 30
              }
            }, {
              name: "旋钮",
              type: "angle",
              data: {
                clue: "#angle-{0}",
                precision: 30
              }
            }],
            interact: [{
              type: "click",
              preClue: ["#angle-90", "#angle-180"],
              clue: "#转盘锁",
              params: {
                isOnce: !0
              }
            }]
          }, {
            name: "锯子",
            preClue: ["#angle-90", "#angle-180", "#转盘锁"],
            interact: [{
              type: "use",
              target: "排水管",
              audio: "锯木头",
              clue: "#棍子"
            }, {
              type: "use",
              target: "手",
              audio: "锯木头",
              clue: "#手指"
            }]
          }]
        }, {
          name: "电报机",
          desc: "电报机没有装电池，无法使用",
          tip: "需要先从时钟拿到电池",
          type: "morse",
          data: {
            code: "...--/--.../.----",
            preClue: ["#电池>电报机"]
          },
          state: [{
            name: "电报机",
            desc: "电报机发出了哔哔哔的声响",
            tip: "根据书架上的笔记对照摩斯密码得到 「371」",
            preClue: ["#电池>电报机"]
          }]
        }]
      }, {
        name: "时钟",
        desc: "对面墙上的时钟似乎坏掉了，一直卡在三点半",
        nodes: [{
          name: "电池",
          preClue: ["#钥匙>镣铐"],
          interact: [{
            type: "use",
            target: "电报机",
            clue: "#电池>电报机",
            audio: "仪器打开",
            params: {
              isOnce: !0
            }
          }]
        }]
      }, {
        name: "排水管",
        desc: "连接在墙里的排水管，似乎可以用工具锯断",
        state: [{
          name: "棍子",
          preClue: ["#棍子"]
        }],
        interact: [{
          type: "use",
          target: "墙上的钥匙",
          preClue: ["#棍子"],
          clue: "#棍子>墙上的钥匙"
        }]
      }, {
        name: "书架",
        preClue: ["#钥匙>镣铐"],
        nodes: [{
          name: "笔记",
          type: "image",
          data: {
            image: "images/morse.jpg"
          }
        }, {
          name: "日记本",
          nodes: [{
            name: "日记 1",
            type: "text",
            data: {
              text: {
                content: `
<class='highlightTitle'>3月12日</class>

    今天早上我起床后，我从窗外看到一个奇怪的人，他一直盯着我这边看。我有些害怕，于是我关上了窗户。
    中午的时候，就开始收拾我的大铁箱了。这个箱子能够保存我所有心爱的东西。前些日子还上了密码锁，为了怕忘记我把密码记到电报机里，然后再加上我的生日，我太聪明了。哈哈。
                      `
              }
            }
          }, {
            name: "日记 2",
            type: "text",
            data: {
              text: {
                content: `
<class='highlightTitle'>3月13日</class>

    今天我去订一块生日蛋糕。我去了附近的面包店，挑选了一块巧克力蛋糕。店员告诉我，明天会将蛋糕送上门，我很期待。
    在回家的路上，我又注意到了那个怪人。他一直跟在我后面，让我感到很不安。于是我开始加快步伐，试图摆脱他的跟踪。最终，我回到了家里，感觉好累。
                      `
              }
            }
          }, {
            name: "日记 3",
            type: "text",
            data: {
              text: {
                content: `
<class='highlightTitle'>3月14日</class>

    早上有人敲门，我从猫眼看没有人，不知道是谁在敲门。
    昨天订的蛋糕也一直没有送过来。。。
                      `
              }
            }
          }]
        }]
      }, {
        name: "大铁箱",
        preClue: ["#钥匙>镣铐"],
        nodes: [{
          name: "密码锁",
          tip: "根据摩斯密码和日记得知的生日相加得到 「685」",
          data: {
            lockClue: "#大铁箱密码锁"
          },
          nodes: [{
            name: "0",
            type: "password",
            data: {
              text: "1",
              clue: "#pass1-{0}"
            }
          }, {
            name: "0",
            type: "password",
            data: {
              text: "2",
              clue: "#pass2-{0}"
            }
          }, {
            name: "0",
            type: "password",
            data: {
              text: "3",
              clue: "#pass3-{0}"
            }
          }],
          interact: [{
            type: "click",
            clue: "#大铁箱密码锁",
            preClue: ["#pass1-6", "#pass2-8", "#pass3-5"],
            params: {
              isOnce: !0
            }
          }]
        }, {
          name: "尸体",
          desc: "一具尸体被锁在铁箱里",
          preClue: ["#大铁箱密码锁"],
          audio: "打开铁门",
          nodes: [{
            name: "手",
            desc: "尸体塞在箱子里无法移动",
            tip: "因为尸体无法移动，所以需要先用锯子得到手指",
            state: [{
              name: "手指",
              preClue: ["#手指"]
            }],
            interact: [{
              type: "use",
              target: "指纹锁",
              clue: "#手指>指纹锁",
              preClue: ["#手指"]
            }]
          }, {
            name: "脸",
            desc: "尸体脸上的表情惊恐又痛苦"
          }]
        }]
      }, {
        name: "锁着的门",
        preClue: ["#钥匙>镣铐"],
        state: [{
          name: "出口",
          preClue: ["#手指>指纹锁"]
        }],
        nodes: [{
          name: "指纹锁",
          data: {
            lockClue: "#手指>指纹锁"
          }
        }],
        interact: [{
          type: "click",
          clue: "@通关",
          preClue: ["#手指>指纹锁"]
        }]
      }]
    }]
  }
  , Ii = {
    name: "mission3",
    missionName: "第三关",
    nextMission: "mission4",
    bgm: {
      雷雨: .5
    },
    nodes: [{
      point: "center",
      name: "实验室",
      desc: "空气中弥漫着一股奇怪的气味",
      nodes: [{
        name: "锁住的门",
        desc: "无法打开，需要先解除门禁系统",
        data: {
          lockClue: "#锁住的门"
        },
        state: [{
          name: "出口",
          desc: "门已经打开",
          preClue: "#锁住的门"
        }],
        interact: [{
          type: "click",
          clue: "@通关",
          preClue: "#锁住的门"
        }]
      }, {
        name: "配电箱",
        state: [{
          name: "配电箱",
          desc: "已经恢复电力供应",
          preClue: ["#电源开关"]
        }],
        nodes: [{
          name: "电源开关",
          tip: `根据连线说明里的出入口角度调整连线角度
例如黄色入口和出口是 180° 向下的`,
          data: {
            noRefreshData: !0,
            lockClue: "#电源开关"
          },
          nodes: [{
            name: "蓝色连线",
            type: "angle",
            data: {
              clue: "#blue-angle-{0}",
              precision: 30,
              lineColor: "#5271ff"
            }
          }, {
            name: "红色连线",
            type: "angle",
            data: {
              clue: "#red-angle-{0}",
              precision: 30,
              lineColor: "#ff3131"
            }
          }, {
            name: "黄色连线",
            type: "angle",
            data: {
              clue: "#yellow-angle-{0}",
              precision: 30,
              lineColor: "#ffde59"
            }
          }],
          interact: [{
            type: "click",
            preClue: ["#blue-angle-330", "#red-angle-240", "#yellow-angle-180"],
            clue: "#电源开关",
            audio: "恢复供电",
            params: {
              isOnce: !0
            }
          }]
        }, {
          name: "连线说明",
          desc: "配电箱的门背面贴着一张纸",
          type: "image",
          data: {
            image: "images/配电箱连线.jpg"
          }
        }]
      }, {
        name: "实验台",
        nodes: [{
          name: "控制终端",
          desc: "没有电力供应，无法使用",
          state: [{
            name: "控制终端",
            desc: "终端连接着一个数字键盘",
            preClue: "#电源开关"
          }],
          nodes: [{
            name: "按钮",
            desc: "终端显示屏上出现了 「78963」",
            tip: "按数字小键盘的按键连线，是 「7」",
            preClue: "#电源开关",
            data: {
              activeColor: "#ffde59"
            }
          }, {
            name: "按钮",
            tip: "按数字小键盘的按键连线，是 「1」",
            preClue: "#电源开关",
            desc: "终端显示屏上出现了 「963」",
            data: {
              activeColor: "#ff3131"
            }
          }, {
            name: "按钮",
            tip: "按数字小键盘的按键连线，是 「4」",
            preClue: "#电源开关",
            desc: "终端显示屏上出现了 「7456963」",
            data: {
              activeColor: "#5271ff"
            }
          }],
          interact: [{
            type: "click",
            preClue: "#图形谜题",
            clue: "#控制终端"
          }]
        }, {
          name: "保险柜",
          nodes: [{
            name: "密码锁",
            data: {
              lockClue: "#保险柜"
            },
            interact: [{
              type: "click",
              preClue: ["#yellow-7", "#red-1", "#blue-4"],
              clue: "#保险柜",
              params: {
                isOnce: !0
              },
              audio: "解锁2"
            }],
            nodes: [{
              name: "0",
              type: "password",
              data: {
                color: "#ffde59",
                clue: "#yellow-{0}"
              }
            }, {
              name: "0",
              type: "password",
              data: {
                color: "#ff3131",
                clue: "#red-{0}"
              }
            }, {
              name: "0",
              type: "password",
              data: {
                color: "#5271ff",
                clue: "#blue-{0}"
              }
            }]
          }, {
            name: "实验日记",
            preClue: "#保险柜",
            type: "image",
            data: {
              image: "images/实验日记1.jpg"
            },
            state: [{
              name: "实验日记",
              preClue: "#白纸>紫外线灯",
              data: {
                image: "images/实验日记2.jpg"
              }
            }],
            interact: [{
              type: "use",
              target: "紫外线灯",
              clue: "#白纸>紫外线灯"
            }]
          }, {
            name: "探测仪",
            desc: "越靠近金属，闪烁频率越快",
            tip: "挪动探测仪节点，声音或灯泡闪烁的频率越快越接近，找到一个看不见的「隐藏门」节点",
            preClue: "#保险柜",
            type: "detector",
            data: {
              target: "隐藏门"
            },
            interact: [{
              type: "use",
              target: "隐藏门",
              clue: "#隐藏门",
              params: {
                isOnce: !0
              }
            }]
          }, {
            name: "隐藏门",
            key: "隐藏门",
            desc: "看起来只是普通的一面墙",
            data: {
              noRefreshData: !0,
              independent: !0,
              stealthUntilClue: "#隐藏门",
              distance: Math.random() * 30 + 100
            },
            nodes: [{
              name: "密室",
              preClue: "#隐藏门",
              audio: "打开衣柜",
              interact: [{
                type: "click",
                clue: "#密室"
              }],
              nodes: [{
                name: "紫外线灯",
                desc: "一盏紫外线灯，也许可以用来照出隐藏的笔迹"
              }, {
                name: "神秘仪器",
                desc: "桌子上摆满了各种神秘的仪器",
                nodes: [{
                  name: "药水调配器",
                  tip: "需要先将紫外线灯照射实验日记，找到真正的解药顺序",
                  type: "color-sort",
                  data: {
                    colorCount: 4,
                    clue: "#药水调配",
                    targetEntry: ["blue", "green", "red", "yellow"]
                  },
                  nodes: [{
                    name: "解药",
                    desc: "调配出来的药剂，也许有什么功效",
                    audio: "叮",
                    interact: [{
                      type: "use",
                      target: "丧尸",
                      clue: "#解药",
                      params: {
                        isOnce: !0
                      }
                    }]
                  }]
                }, {
                  name: "药箱",
                  desc: "装满各种颜色药剂的药箱",
                  audio: "门-开锁",
                  nodes: [{
                    name: "红色药剂",
                    data: {
                      forColorSort: {
                        name: "药水调配器",
                        color: "red",
                        entry: "red"
                      },
                      activeColor: "#ff3131"
                    }
                  }, {
                    name: "蓝色药剂",
                    data: {
                      forColorSort: {
                        name: "药水调配器",
                        color: "blue",
                        entry: "blue"
                      },
                      activeColor: "#5271ff"
                    }
                  }, {
                    name: "绿色药剂",
                    data: {
                      forColorSort: {
                        name: "药水调配器",
                        color: "green",
                        entry: "green"
                      },
                      activeColor: "#609966"
                    }
                  }, {
                    name: "黄色药剂",
                    data: {
                      forColorSort: {
                        name: "药水调配器",
                        color: "yellow",
                        entry: "yellow"
                      },
                      activeColor: "#ffde59"
                    }
                  }]
                }]
              }, {
                name: "丧尸",
                desc: "穿着白大褂的丧尸拷在角落发狂，无法轻易靠近",
                audio: "丧尸",
                state: [{
                  name: "尸体",
                  desc: "一具干瘪的尸体",
                  preClue: "#解药"
                }],
                nodes: [{
                  name: "白大褂",
                  preClue: "#解药",
                  nodes: [{
                    name: "ID卡",
                    desc: "ID 卡上写着 「实验人员，人员编号 996」",
                    interact: [{
                      type: "use",
                      target: "锁住的门",
                      clue: "#锁住的门"
                    }]
                  }]
                }]
              }]
            }]
          }]
        }]
      }]
    }]
  }
  , Bi = {
    name: "mission4",
    missionName: "第四关",
    nextMission: "mission5",
    bgm: {
      风: .1,
      滴水: 1
    },
    nodes: [{
      point: "center",
      name: "牢房",
      desc: "灰暗的牢房，四周都是墙壁",
      state: [],
      nodes: [{
        name: "墙壁",
        desc: "上面刻画着各种图案，其中包含着 「1/3/2」",
        nodes: [{
          name: "裂缝",
          desc: "墙上有一道裂缝，里面似乎有什么东西",
          type: "breakable",
          data: {
            clue: "#裂缝",
            needInteractCount: 5,
            audio: "凿"
          },
          nodes: [{
            name: "金币",
            preClue: "#裂缝",
            tip: "给予神秘人换取出逃的物品",
            audio: "金币掉落",
            interact: [{
              type: "use",
              target: "神秘人",
              clue: "#金币>神秘人",
              params: {
                isOnce: !0
              }
            }]
          }]
        }]
      }, {
        name: "铁窗",
        desc: "竖着好几根铁棍的铁窗，能敲出清脆的响声",
        tip: "根据墙壁的提示，依次敲打铁窗1下、3下、2下",
        type: "knock",
        state: [{
          name: "铁窗",
          preClue: "#铁窗-1-3-2"
        }],
        data: {
          knockCount: 3,
          clue: "#铁窗-{0}-{1}-{2}",
          stopClue: "#铁窗-1-3-2",
          audio: "敲铁"
        },
        nodes: [{
          name: "铁棍",
          preClue: "#钳子>铁窗",
          data: {
            autoAdd: !0
          },
          state: [{
            name: "铁棍",
            desc: "铁棍的一端吸附着磁铁",
            preClue: "#磁铁>铁棍"
          }],
          interact: [{
            type: "use",
            target: "老鼠洞",
            preClue: "#磁铁>铁棍",
            clue: "#铁棍>老鼠洞"
          }]
        }]
      }, {
        name: "神秘人",
        desc: "出现在窗外的神秘人",
        data: {
          noRefreshData: !0,
          independent: !0,
          stealthUntilClue: "#铁窗-1-3-2",
          removeIfClue: "#宝石>神秘人",
          distance: 120
        },
        nodes: [{
          name: "钳子",
          preClue: "#金币>神秘人",
          data: {
            autoAdd: !0,
            independent: !0
          },
          interact: [{
            type: "use",
            target: "铁窗",
            clue: "#钳子>铁窗",
            params: {
              isOnce: !0
            }
          }]
        }]
      }, {
        name: "锁住的牢门",
        desc: "很厚的一扇牢门，最底下有能递东西的缺口",
        state: [{
          name: "牢门",
          desc: "需要等待一定的时机才能出逃",
          preClue: "#钥匙>牢门"
        }],
        data: {
          lockClue: "#钥匙>牢门"
        },
        interact: [{
          type: "click",
          preClue: ["#钥匙>牢门", "#angle-60", "#angle-270"],
          clue: "@通关"
        }],
        nodes: [{
          name: "磁铁",
          desc: "掉落在门旁的磁铁，也许有什么用",
          interact: [{
            type: "use",
            target: "铁棍",
            clue: "#磁铁>铁棍",
            params: {
              isOnce: !0
            }
          }]
        }, {
          name: "牢饭",
          preClue: "#宝石>神秘人",
          audio: "铁盘滑动",
          nodes: [{
            name: "钥匙",
            desc: "藏在牢饭里的钥匙",
            interact: [{
              type: "use",
              target: "锁住的牢门",
              clue: "#钥匙>牢门",
              params: {
                isOnce: !0
              }
            }]
          }, {
            name: "纸条",
            desc: "藏在牢饭里的纸条，上面写着 「02:45」"
          }]
        }]
      }, {
        name: "木床",
        desc: "地上放着的一张破破烂烂的木床",
        tip: "需要拿到铁棍，再用铁棍敲击三次木床",
        type: "breakable",
        data: {
          clue: "#木床",
          needInteractCount: 3,
          breakTarget: "铁棍",
          audio: "敲木板"
        },
        nodes: [{
          name: "锁住的铁箱",
          desc: "藏在木床底下的铁箱，需要钥匙才能打开",
          preClue: "#木床",
          state: [{
            name: "铁箱",
            preClue: "#铁箱钥匙>锁住的铁箱"
          }],
          nodes: [{
            name: "宝石",
            desc: "一袋璀璨的宝石，能值很多钱",
            tip: "给予神秘人换取出逃的物品",
            preClue: "#铁箱钥匙>锁住的铁箱",
            interact: [{
              type: "use",
              target: "神秘人",
              clue: "#宝石>神秘人",
              params: {
                isOnce: !0
              }
            }]
          }, {
            name: "怀表",
            preClue: "#铁箱钥匙>锁住的铁箱",
            tip: "需要将指针调整到 02:45 的方向才能打开牢房门",
            data: {
              noRefreshData: !0
            },
            nodes: [{
              name: "时针",
              type: "angle",
              data: {
                clue: "#angle-{0}",
                precision: 30
              }
            }, {
              name: "分针",
              type: "angle",
              data: {
                clue: "#angle-{0}",
                precision: 30
              }
            }]
          }]
        }]
      }, {
        name: "老鼠洞",
        desc: "地上有老鼠洞，手无法伸进去",
        tip: "需要带磁铁的铁棍才能拿到里面的东西",
        nodes: [{
          name: "铁箱钥匙",
          preClue: "#铁棍>老鼠洞",
          data: {
            autoAdd: !0
          },
          interact: [{
            type: "use",
            target: "锁住的铁箱",
            clue: "#铁箱钥匙>锁住的铁箱",
            params: {
              isOnce: !0
            }
          }]
        }]
      }]
    }]
  }
  , Ni = {
    name: "mission5",
    missionName: "第五关",
    nextMission: "mission6",
    cutscene: [{
      type: "text",
      desc: "炸弹爆炸，逃脱失败",
      preClue: "@失败",
      time: 2e3,
      vibrate: "heavy"
    }],
    bgm: {},
    nodes: [{
      point: "center",
      name: "房间",
      desc: "看起来是只有简单几件家具的休息室",
      nodes: [{
        name: "窗户",
        desc: "无法打开的窗户，太阳正在缓缓落下"
      }, {
        name: "垃圾桶",
        nodes: [{
          name: "碎纸",
          type: "image",
          data: {
            image: "images/碎纸.png"
          }
        }]
      }, {
        name: "炸弹",
        desc: "结实的军火箱，中间的玻璃能看到炸弹倒计时",
        type: "timer",
        data: {
          time: 60 * 5,
          stopClue: "#解除炸弹",
          overClue: "@失败",
          effectAudio: "bomb-di",
          overAudio: "bomb-boom"
        },
        nodes: [{
          name: "锁住的军火箱",
          desc: "锁住了，需要钥匙才能打开",
          data: {
            lockClue: "#军火箱钥匙>锁住的军火箱"
          },
          state: [{
            name: "军火箱",
            preClue: "#军火箱钥匙>锁住的军火箱"
          }],
          nodes: [{
            name: "引爆装置",
            desc: "在解除炸弹前，最好不要去拆它",
            state: [{
              name: "引爆装置",
              desc: "中间嵌着柱形钥匙，似乎能搞下来",
              preClue: "#解除炸弹"
            }],
            preClue: ["#军火箱钥匙>锁住的军火箱"],
            nodes: [{
              name: "0",
              type: "password",
              data: {
                text: "1",
                clue: "#pass1-{0}"
              }
            }, {
              name: "0",
              type: "password",
              data: {
                text: "2",
                clue: "#pass2-{0}"
              }
            }, {
              name: "0",
              type: "password",
              data: {
                text: "3",
                clue: "#pass3-{0}"
              }
            }, {
              name: "柱形钥匙",
              preClue: ["#螺丝刀>引爆装置"],
              data: {
                autoAdd: !0
              },
              interact: [{
                type: "use",
                target: "书架",
                clue: "#柱形钥匙>书架",
                params: {
                  isOnce: !0
                }
              }]
            }],
            interact: [{
              type: "click",
              clue: "#解除炸弹",
              preClue: ["#pass1-4", "#pass2-3", "#pass3-1"]
            }]
          }]
        }]
      }, {
        name: "桌子",
        desc: "一个木质的办公桌",
        nodes: [{
          name: "电脑",
          nodes: [{
            name: "开机密码",
            tip: "根据垃圾桶的碎纸提示密码为红2黄3蓝9",
            data: {
              lockClue: "#开机密码"
            },
            interact: [{
              type: "click",
              preClue: ["#yellow-3", "#red-2", "#blue-9"],
              clue: "#开机密码",
              params: {
                isOnce: !0
              },
              audio: "开机"
            }],
            nodes: [{
              name: "0",
              type: "password",
              data: {
                color: "#ffde59",
                clue: "#yellow-{0}"
              }
            }, {
              name: "0",
              type: "password",
              data: {
                color: "#ff3131",
                clue: "#red-{0}"
              }
            }, {
              name: "0",
              type: "password",
              data: {
                color: "#5271ff",
                clue: "#blue-{0}"
              }
            }]
          }, {
            name: "邮箱",
            preClue: "#开机密码",
            nodes: [{
              name: "邮件1",
              type: "text",
              data: {
                text: {
                  title: "指示邮件",
                  content: `
我们的秘密基地已被发现，立即使用炸弹炸毁此处，并且摧毁内部数据文件。
                          `
                }
              }
            }, {
              name: "邮件2",
              type: "text",
              data: {
                text: {
                  title: "炸弹说明",
                  content: `
<class='highlight'>炸弹安装：</class>
1. 组织内部的柱形钥匙放入引爆装置
2. 装上盖板
3. 输入行动代号
4. 设定倒计时启动炸弹

<class='highlight'>炸弹解除：</class>
将行动代号反转后输入即可解除，切记收到行动代号后立即销毁邮件。
                          `
                }
              }
            }, {
              name: "邮件3",
              type: "text",
              data: {
                text: {
                  title: "行动代号",
                  content: `
<class='remark'>-- 内容已销毁 --</class>
                          `
                }
              }
            }]
          }, {
            name: "加密文件",
            preClue: "#开机密码",
            desc: "文件内容已被加密，需要密钥解密",
            state: [{
              name: "数据文件",
              desc: "邪恶组织的重要数据文件",
              preClue: ["#密钥>加密文件"]
            }],
            type: "text",
            data: {
              lockClue: "#加密文件",
              preClue: ["#密钥>加密文件"],
              text: {
                title: "组织内部文件",
                content: `
<class='highlight'>行动计划：</class>

代号134：
> 在基地 6 层南边的休息室安置炸弹
> 休息室密码为房间号

<class='remark'>-- 省略其他计划 --</class>

人员名单：

<class='remark'>-- 省略 --</class>
                      `
              }
            }
          }]
        }, {
          name: "便签",
          tip: "使用铅笔可以找到行动代号痕迹",
          desc: "一沓便签，已经被撕掉了一些",
          state: [{
            name: "便签",
            desc: "用铅笔涂了后，能看到写过 「代号134」 的痕迹",
            preClue: ["#铅笔>便签"]
          }]
        }, {
          name: "抽屉",
          nodes: [{
            name: "螺丝刀",
            interact: [{
              type: "use",
              target: "引爆装置",
              preClue: ["#解除炸弹"],
              clue: "#螺丝刀>引爆装置"
            }, {
              type: "use",
              target: "通风口",
              clue: "#螺丝刀>通风口"
            }]
          }, {
            name: "铅笔",
            interact: [{
              type: "use",
              target: "便签",
              clue: "#铅笔>便签",
              desc: "用铅笔涂了后，能看到写过 「代号134」 的痕迹"
            }]
          }]
        }]
      }, {
        name: "通风口",
        tip: "可以使用螺丝刀打开通风口",
        desc: "一个不大的通风口，被百叶窗盖住了",
        state: [{
          name: "通风口",
          desc: "百叶窗已经打开了",
          preClue: ["#螺丝刀>通风口"]
        }],
        nodes: [{
          name: "军火箱钥匙",
          preClue: ["#螺丝刀>通风口"],
          interact: [{
            type: "use",
            target: "锁住的军火箱",
            clue: "#军火箱钥匙>锁住的军火箱",
            params: {
              isOnce: !0
            }
          }]
        }]
      }, {
        name: "锁住的门",
        desc: "无法打开，需要先解除门禁系统",
        data: {
          lockClue: "#锁住的门"
        },
        state: [{
          name: "出口",
          desc: "门已经打开",
          preClue: "#锁住的门"
        }],
        interact: [{
          type: "click",
          clue: "@通关",
          preClue: "#锁住的门"
        }],
        nodes: [{
          name: "门禁密码",
          tip: "根据窗户能看到落日得知窗户朝西，再根据平面图与内部文件得知密码为 605",
          preClue: ["#ID卡>锁住的门"],
          data: {
            lockClue: "#锁住的门"
          },
          nodes: [{
            name: "0",
            type: "password",
            data: {
              text: "1",
              clue: "#门禁密码1-{0}"
            }
          }, {
            name: "0",
            type: "password",
            data: {
              text: "2",
              clue: "#门禁密码2-{0}"
            }
          }, {
            name: "0",
            type: "password",
            data: {
              text: "3",
              clue: "#门禁密码3-{0}"
            }
          }],
          interact: [{
            type: "click",
            preClue: ["#门禁密码1-6", "#门禁密码2-0", "#门禁密码3-5"],
            clue: "#锁住的门",
            params: {
              isOnce: !0
            }
          }]
        }]
      }, {
        name: "书架",
        desc: "放着很多书的书架，其中两本书中间有个奇怪的六边形洞",
        nodes: [{
          name: "《神秘百慕大》",
          desc: "封面上写着 「A25-B5-C5」"
        }, {
          name: "《球形闪电》",
          desc: "封面上写着 「A5-B5-C5-D2」"
        }, {
          name: "《星际迷航》",
          desc: "封面上写着 「A245-B5-C5」"
        }, {
          name: "暗室",
          desc: "插入柱形钥匙后，书架移动出现了暗室",
          preClue: ["#柱形钥匙>书架"],
          nodes: [{
            name: "海报",
            desc: "贴在墙上的奇怪海报",
            tip: "根据书架上的书分别填入得到对应密码",
            type: "image",
            data: {
              image: "images/mission5-post.jpg"
            }
          }, {
            name: "楼层平面图",
            desc: "贴在门上的楼层平面图",
            type: "image",
            data: {
              image: "images/mission5-floor.jpg"
            }
          }, {
            name: "保险柜",
            nodes: [{
              name: "密码锁",
              tip: "书名对应着图形，《神秘百慕大》代表三角形，《球形闪电》代表圆形，《星际穿越》代表五角星",
              data: {
                lockClue: "#保险柜密码锁"
              },
              nodes: [{
                name: "0",
                type: "password",
                data: {
                  text: "▲",
                  clue: "#保险柜1-{0}"
                }
              }, {
                name: "0",
                type: "password",
                data: {
                  text: "●",
                  clue: "#保险柜2-{0}"
                }
              }, {
                name: "0",
                type: "password",
                data: {
                  text: "★",
                  clue: "#保险柜3-{0}"
                }
              }],
              interact: [{
                type: "click",
                preClue: ["#保险柜1-5", "#保险柜2-3", "#保险柜3-6"],
                clue: "#保险柜密码锁",
                params: {
                  isOnce: !0
                }
              }]
            }, {
              name: "密钥",
              desc: "一大串复杂的密钥",
              preClue: ["#保险柜密码锁"],
              interact: [{
                type: "use",
                target: "加密文件",
                clue: "#密钥>加密文件",
                params: {
                  isOnce: !0
                }
              }]
            }, {
              name: "ID卡",
              preClue: ["#保险柜密码锁"],
              interact: [{
                type: "use",
                target: "锁住的门",
                clue: "#ID卡>锁住的门"
              }]
            }]
          }]
        }]
      }]
    }]
  }
  , Ui = {
    name: "mission6",
    missionName: "第六关",
    nextMission: "mission7",
    bgm: {
      地下滴水: .8
    },
    nodes: [{
      point: "center",
      name: "地下室",
      desc: "昏暗的地下室，头顶的灯泡在闪烁着微弱的光",
      nodes: [{
        name: "锁住的门",
        desc: "通往地面的门，锁住了无法打开",
        data: {
          lockClue: "#锁住的门"
        },
        state: [{
          name: "出口",
          preClue: ["#锁住的门"]
        }],
        nodes: [{
          name: "密码锁",
          data: {
            lockClue: "#锁住的门"
          },
          nodes: [{
            name: "0",
            type: "password",
            data: {
              text: "1",
              clue: "#锁住的门1-{0}"
            }
          }, {
            name: "0",
            type: "password",
            data: {
              text: "2",
              clue: "#锁住的门2-{0}"
            }
          }, {
            name: "0",
            type: "password",
            data: {
              text: "3",
              clue: "#锁住的门3-{0}"
            }
          }],
          interact: [{
            type: "click",
            preClue: ["#锁住的门1-4", "#锁住的门2-1", "#锁住的门3-9"],
            clue: "#锁住的门",
            params: {
              isOnce: !0
            }
          }]
        }],
        interact: [{
          type: "click",
          clue: "@通关",
          preClue: "#锁住的门"
        }]
      }, {
        name: "桌子",
        desc: "一张破旧的木桌",
        nodes: [{
          name: "空酒瓶",
          desc: "散落在桌上的空酒瓶",
          state: [{
            name: "装满水的酒瓶",
            preClue: "#装满水的酒瓶"
          }],
          interact: [{
            type: "use",
            target: "排水口",
            clue: "#装满水的酒瓶>排水口",
            preClue: ["#装满水的酒瓶"]
          }]
        }, {
          name: "笔记本电脑",
          desc: "似乎是我带来的笔记本电脑，但是已经没电了",
          state: [{
            name: "笔记本电脑",
            preClue: ["#电源线>笔记本电脑"]
          }],
          nodes: [{
            name: "键盘",
            tip: "有酒精的味道代表有人喝酒并把酒弄在了键盘上，加药品粉末能看到按键痕迹",
            desc: "脏兮兮的键盘，上面有一股酒精的味道",
            state: [{
              name: "键盘",
              desc: "洒上粉末后吹掉，0、2、7 按键仍残留粉末",
              preClue: "#药品>键盘"
            }]
          }, {
            name: "开机密码",
            tip: "根据键盘提示得到 0、2、7 三个数字，再根据开机密码提示可知密码为 702",
            preClue: "#电源线>笔记本电脑",
            desc: "密码提示：不被 5 整除的三位数的偶数",
            data: {
              lockClue: "#开机密码"
            },
            nodes: [{
              name: "0",
              type: "password",
              data: {
                text: "1",
                clue: "#开机密码1-{0}"
              }
            }, {
              name: "0",
              type: "password",
              data: {
                text: "2",
                clue: "#开机密码2-{0}"
              }
            }, {
              name: "0",
              type: "password",
              data: {
                text: "3",
                clue: "#开机密码3-{0}"
              }
            }],
            interact: [{
              type: "click",
              preClue: ["#开机密码1-7", "#开机密码2-0", "#开机密码3-2"],
              clue: "#开机密码",
              audio: "开机",
              params: {
                isOnce: !0
              }
            }]
          }, {
            name: "已销毁的数据",
            desc: "看起来数据已经被销毁了，无法使用",
            preClue: ["#电源线>笔记本电脑", "#开机密码"]
          }, {
            name: "内部数据",
            desc: "数据量庞大的组织内部数据，不检索很难找到有用的信息",
            preClue: ["#电源线>笔记本电脑", "#开机密码", "#U盘>笔记本电脑"],
            nodes: [{
              name: "检索",
              tip: "根据行动指令检索人员编号 138 得到此人资料",
              nodes: [{
                name: "0",
                type: "password",
                data: {
                  text: "1",
                  clue: "#检索1-{0}"
                }
              }, {
                name: "0",
                type: "password",
                data: {
                  text: "2",
                  clue: "#检索2-{0}"
                }
              }, {
                name: "0",
                type: "password",
                data: {
                  text: "3",
                  clue: "#检索3-{0}"
                }
              }],
              interact: [{
                type: "click",
                preClue: ["#检索1-1", "#检索2-3", "#检索3-8"],
                clue: "#检索138"
              }, {
                type: "click",
                preClue: ["#检索1-4", "#检索2-4", "#检索3-4"],
                clue: "#检索444"
              }, {
                type: "click",
                preClue: ["#检索1-9", "#检索2-9", "#检索3-6"],
                clue: ["#检索996", "%mission6-996"]
              }]
            }, {
              name: "编号 138 资料",
              preClue: ["#检索138"],
              type: "text",
              data: {
                text: {
                  title: "人员编号138",
                  content: `
直属于编号 444 的执行人员，负责执行铲除、爆破、销毁证据等任务。
                          `
                }
              }
            }, {
              name: "编号 444 资料",
              preClue: ["#检索444"],
              type: "text",
              data: {
                text: {
                  title: "人员编号444",
                  content: `
打入特工机构的高级人员，在特工机构化名 DD，负责获取特工机构的卧底信息，对组织有害的特工进行铲除。

住处：AA 市区 BB 路 419 号 XX 山庄。
                          `
                }
              }
            }, {
              name: "编号 996 资料",
              preClue: ["#检索996"],
              type: "text",
              data: {
                text: {
                  title: "人员编号996",
                  content: `
高级实验人员，负责研发人体变异的生化武器。

目前人员下落不明，实验资料丢失，计划终止。
                          `
                }
              }
            }]
          }]
        }]
      }, {
        name: "工作台",
        nodes: [{
          name: "水龙头",
          interact: [{
            type: "use",
            target: "空酒瓶",
            clue: "#装满水的酒瓶"
          }]
        }, {
          name: "药品",
          desc: "一种粉末状的药品，上面写着能对记忆进行清除",
          interact: [{
            type: "use",
            target: "键盘",
            clue: "#药品>键盘"
          }]
        }, {
          name: "铁盒",
          desc: "一个结实的铁盒，上面用密码锁锁着",
          nodes: [{
            name: "密码锁",
            data: {
              lockClue: "#密码锁"
            },
            nodes: [{
              name: "0",
              type: "password",
              data: {
                text: "▲",
                clue: "#密码锁3-{0}"
              }
            }, {
              name: "0",
              type: "password",
              data: {
                text: "●",
                clue: "#密码锁0-{0}"
              }
            }, {
              name: "0",
              type: "password",
              data: {
                text: "■",
                clue: "#密码锁4-{0}"
              }
            }],
            interact: [{
              type: "click",
              preClue: ["#密码锁3-5", "#密码锁4-2", "#密码锁0-3"],
              clue: "#密码锁",
              params: {
                isOnce: !0
              }
            }]
          }, {
            name: "电源线",
            preClue: "#密码锁",
            desc: "一根电源线，看起来是用来给电脑供电的",
            interact: [{
              type: "use",
              target: "笔记本电脑",
              clue: "#电源线>笔记本电脑",
              params: {
                isOnce: !0
              }
            }]
          }, {
            name: "个人档案",
            tip: "生日 512 是手机的锁屏密码",
            desc: "档案上面贴着我的照片，似乎是我的档案",
            preClue: "#密码锁",
            type: "text",
            data: {
              text: {
                title: "个人档案",
                content: `
姓名：张伟
性别：男
出生日期：1992年5月12日
身份：特工
                      `
              }
            }
          }, {
            name: "行动指令",
            tip: "编号 138 为内部数据检索时使用",
            preClue: "#密码锁",
            type: "text",
            data: {
              text: {
                title: "行动指令",
                content: `
上次的爆炸行动计划未能成功铲除此人，还让他获取组织的内部数据。

我将会安排此人到 XX 山庄交接数据，你把他打晕后关入地下室，并将数据全部销毁掉。(地下室密码为门牌号)

上层已高度重视此人，不要直接杀掉，先用秘密药物去掉他的记忆，确保对组织无害后再放出。
                      `,
                name: "To 编号138"
              }
            }
          }]
        }]
      }, {
        name: "排水口",
        tip: "使用手机能看到里面有东西，空酒瓶用水龙头装水后倒入即可",
        desc: "一个小小洞口的排水口，看不清里面有什么",
        state: [{
          name: "排水口",
          desc: "看起来是堵死的排水口，底部有什么东西",
          preClue: "#手机>排水口"
        }, {
          name: "排水口",
          preClue: "#装满水的酒瓶>排水口"
        }],
        nodes: [{
          name: "纸团",
          desc: "从排水口浮上来的纸团",
          preClue: "#装满水的酒瓶>排水口",
          state: [{
            name: "纸条",
            tip: "第一个数字代表角的数量，第二个数字代表对应密码。例如 35 代表三角形的密码为 5。",
            desc: "皱巴巴的纸条上写着 「35-42-03」",
            preClue: "#纸条"
          }],
          interact: [{
            type: "click",
            clue: "#纸条",
            desc: "皱巴巴的纸条上写着 「35-42-03」"
          }]
        }]
      }, {
        name: "背包",
        desc: "靠在墙边的背包，似乎是我的",
        nodes: [{
          name: "手机",
          desc: "一部智能手机，壁纸上的人是我自己。手机没有信号",
          nodes: [{
            name: "锁屏密码",
            tip: "因为是我的手机，后续得到个人档案后输入生日即可",
            desc: "因为失忆记不起来锁屏密码了",
            data: {
              lockClue: "#锁屏密码"
            },
            nodes: [{
              name: "0",
              type: "password",
              data: {
                text: "1",
                clue: "#锁屏密码1-{0}"
              }
            }, {
              name: "0",
              type: "password",
              data: {
                text: "2",
                clue: "#锁屏密码2-{0}"
              }
            }, {
              name: "0",
              type: "password",
              data: {
                text: "3",
                clue: "#锁屏密码3-{0}"
              }
            }],
            interact: [{
              type: "click",
              preClue: ["#锁屏密码1-5", "#锁屏密码2-1", "#锁屏密码3-2"],
              clue: "#锁屏密码",
              params: {
                isOnce: !0
              }
            }]
          }, {
            name: "短信",
            preClue: "#锁屏密码",
            nodes: [{
              name: "发送短信1",
              type: "text",
              data: {
                text: {
                  title: "发送短信",
                  content: `
我已破解了他们的炸弹计划，并且获取了邪恶组织的内部资料。
                          `
                }
              }
            }, {
              name: "接收短信2",
              type: "text",
              data: {
                text: {
                  title: "接收短信",
                  content: `
好的。请于明早到 XX 山庄交接数据。

切记因数据涉及国家安全，不得泄露也不可私自查看。
                          `,
                  name: "From DD"
                }
              }
            }]
          }, {
            name: "备忘录",
            tip: "看完备忘录后再点击打火机会出现暗格，再连点 3 次暗格即可获得 U 盘",
            preClue: "#锁屏密码",
            type: "text",
            data: {
              text: {
                title: "备忘录",
                content: `
我有个外观看起来是打火机，实际上底部有个暗格，只需要连按三次就会弹出 U 盘。

以防万一，我将数据备份到了 U 盘中。
                      `
              }
            },
            interact: [{
              type: "click",
              clue: "#备忘录"
            }]
          }],
          interact: [{
            type: "use",
            target: "排水口",
            clue: "#手机>排水口"
          }]
        }, {
          name: "打火机",
          desc: "一个坏掉的铁制打火机，无法正常点火",
          state: [{
            name: "U盘",
            tip: "插入笔记本电脑中能获得内部数据",
            desc: "一个打火机外形的 U 盘",
            preClue: ["#暗格-3"]
          }],
          nodes: [{
            name: "暗格",
            desc: "在底部有个隐藏的暗格",
            preClue: "#备忘录",
            type: "knock",
            data: {
              knockCount: 1,
              clue: "#暗格-{0}",
              stopClue: "#暗格-3",
              audio: "点击1"
            }
          }],
          interact: [{
            type: "use",
            target: "笔记本电脑",
            preClue: "#暗格-3",
            clue: "#U盘>笔记本电脑",
            params: {
              isOnce: !0
            }
          }]
        }]
      }]
    }]
  }
  , Bs = {
    name: "夜视仪",
    key: "夜视仪",
    preClue: "#床头柜锁",
    type: "switch",
    data: {
      independent: !0,
      triggerType: "click",
      clue: "*夜视仪",
      preClue: "-#电量-0",
      openBorderColor: "#00ff00"
    },
    nodes: [{
      name: "电量",
      key: "电量",
      type: "timer",
      preClue: "*夜视仪",
      data: {
        time: 4 * 60,
        autoAdd: !0,
        startClue: "*夜视仪",
        stopClue: "-*夜视仪",
        overClue: ["@Switch-夜视仪?isOpen=false", "#电量-0"]
      }
    }, {
      name: "电量-隐藏节点",
      key: "电量隐藏节点",
      type: "timer",
      preClue: "*夜视仪",
      data: {
        time: 15,
        autoAdd: !0,
        independent: !0,
        stealthUntilClue: "#电量-隐藏节点",
        startClue: ["*黑暗", "#电量-0"],
        stopClue: "*夜视仪|-#电量-0",
        overClue: "#失败-夜视仪"
      }
    }]
  }