const  wi = {
    name: "mission1",
    missionName: "绗�涓�鍏�",
    nextMission: "mission2",
    bgm: {
      闆�: .3,
      椋�: .5
    },
    mask: [{
      type: "foreground",
      background: "#000000",
      alpha: .5,
      showClue: ["-#娌圭伅"]
    }],
    nodes: [{
      point: "center",
      name: "榛戞殫",
      desc: "鍛ㄥ洿涓�鐗囬粦鏆楋紝闇�瑕佸厜婧愭墠鑳界湅娓呭懆鍥淬��",
      state: [{
        name: "鐮村眿",
        preClue: ["#娌圭伅"]
      }],
      nodes: [{
        name: "鍦版澘",
        desc: "濂藉儚鏈変粈涔堜笢瑗挎暎钀藉湪鍦颁笂",
        nodes: [{
          name: "鐏�鏌�",
          interact: [{
            type: "use",
            target: "鏈�鐐圭噧鐨勬补鐏�",
            clue: "#娌圭伅",
            audio: "鐏�鏌寸偣鐏�",
            params: {
              isOnce: !0
            }
          }]
        }]
      }, {
        name: "琛ｆ煖",
        preClue: "#娌圭伅",
        nodes: [{
          name: "瀵嗙爜绠�",
          tip: "鏍规嵁鐢讳綔鎻忕粯鐨勯�滆壊鍜屽�瑰簲鏁板瓧瑙ｅ嚭瀵嗙爜",
          audio: "鎵撳紑琛ｆ煖",
          data: {
            lockClue: "#瀵嗙爜绠�"
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
            name: "閽ュ寵",
            preClue: ["#blue-2", "#red-7", "#green-4"],
            audio: "鎵撳紑閾侀棬",
            interact: [{
              type: "use",
              target: "閿佺潃鐨勯棬",
              clue: "#寮�闂�",
              audio: "闂�-寮�閿�",
              params: {
                isOnce: !0
              }
            }]
          }],
          interact: [{
            type: "click",
            clue: "#瀵嗙爜绠�",
            preClue: ["#blue-2", "#red-7", "#green-4"]
          }]
        }]
      }, {
        name: "婕嗛粦鐨勫��",
        desc: "澧欎笂涓�鐗囨紗榛戯紝鏃犳硶鐪嬫竻",
        state: [{
          name: "澧�",
          desc: "澧欎笂浼间箮鎸傜潃鍑犲箙鐢讳綔",
          preClue: ["#娌圭伅"]
        }],
        nodes: [{
          name: "鐢讳綔",
          desc: "涓�鐗囪敋钃濊壊鐨勫ぉ绌猴紝鐢讳綔涓婂埢鐫� 銆�2銆�",
          preClue: "#娌圭伅"
        }, {
          name: "鐢讳綔",
          desc: "涓�搴ф�ｅ湪鍠峰彂鐨勭伀灞憋紝鐢讳綔涓婂埢鐫� 銆�7銆�",
          preClue: "#娌圭伅"
        }, {
          name: "鐢讳綔",
          desc: "涓�鏈涙棤闄呯殑鑽夊師锛岀敾浣滀笂鍒荤潃 銆�4銆�",
          preClue: "#娌圭伅"
        }]
      }, {
        name: "閿佺潃鐨勯棬",
        desc: "闂ㄤ笂鏈変竴鎶婇攣锛屼綘闇�瑕侀挜鍖欐墠鑳芥墦寮�",
        preClue: "#娌圭伅",
        data: {
          lockClue: "#寮�闂�"
        },
        state: [{
          name: "鍑哄彛",
          desc: "闂ㄥ凡缁忔墦寮�锛屼綘鍙�浠ュ嚭鍘讳簡",
          preClue: ["#寮�闂�"]
        }],
        interact: [{
          type: "click",
          clue: "@閫氬叧",
          preClue: "#寮�闂�"
        }]
      }, {
        name: "鏈�鐐圭噧鐨勬补鐏�",
        desc: "娌圭伅鍙�浠ョ収浜�鍛ㄥ洿鐨勬儏鍐�",
        state: [{
          name: "娌圭伅",
          desc: "娌圭伅宸茬粡鐐逛寒浜嗭紝鍙�浠ョ収浜�鍛ㄥ洿鐨勬儏鍐�",
          preClue: ["#娌圭伅"]
        }]
      }]
    }]
  }
  , Di = {
    name: "mission2",
    missionName: "绗�浜屽叧",
    nextMission: "mission3",
    bgm: {
      椋�: .2
    },
    nodes: [{
      point: "center",
      name: "鎴块棿",
      desc: "涓�涓�鐮寸牬鐑傜儌鐨勬埧闂�",
      nodes: [{
        name: "闀ｉ搻",
        desc: "浣犺��闀ｉ搻閿佷綇浜�",
        state: [{
          name: "瑙ｅ紑鐨勯暎閾�",
          preClue: ["#閽ュ寵>闀ｉ搻"]
        }]
      }, {
        name: "澧欎笂鐨勯挜鍖�",
        desc: "澧欎笂鎮�鎸傜潃閽ュ寵锛岄渶瑕佷竴鏍规�嶅瓙鎵嶈兘鍕惧埌",
        tip: "闇�瑕佸墠缃�閿�瀛愬姞鎺掓按绠℃嬁鍒版�嶅瓙",
        state: [{
          name: "閽ュ寵",
          preClue: ["#妫嶅瓙>澧欎笂鐨勯挜鍖�"]
        }],
        interact: [{
          type: "use",
          target: "闀ｉ搻",
          clue: "#閽ュ寵>闀ｉ搻",
          audio: "瑙ｉ攣1",
          preClue: ["#妫嶅瓙>澧欎笂鐨勯挜鍖�"],
          params: {
            isOnce: !0
          }
        }]
      }, {
        name: "鏌滃瓙",
        nodes: [{
          name: "宸ュ叿绠�",
          audio: "鎵撳紑琛ｆ煖",
          nodes: [{
            name: "杞�鐩橀攣",
            tip: "鏍规嵁鏃堕挓鐨勪笁鐐瑰崐锛屽皢鏃嬮挳杞�鑷� 90掳 鍜� 180掳",
            data: {
              noRefreshData: !0,
              lockClue: "#杞�鐩橀攣"
            },
            nodes: [{
              name: "鏃嬮挳",
              type: "angle",
              data: {
                clue: "#angle-{0}",
                precision: 30
              }
            }, {
              name: "鏃嬮挳",
              type: "angle",
              data: {
                clue: "#angle-{0}",
                precision: 30
              }
            }],
            interact: [{
              type: "click",
              preClue: ["#angle-90", "#angle-180"],
              clue: "#杞�鐩橀攣",
              params: {
                isOnce: !0
              }
            }]
          }, {
            name: "閿�瀛�",
            preClue: ["#angle-90", "#angle-180", "#杞�鐩橀攣"],
            interact: [{
              type: "use",
              target: "鎺掓按绠�",
              audio: "閿�鏈ㄥご",
              clue: "#妫嶅瓙"
            }, {
              type: "use",
              target: "鎵�",
              audio: "閿�鏈ㄥご",
              clue: "#鎵嬫寚"
            }]
          }]
        }, {
          name: "鐢垫姤鏈�",
          desc: "鐢垫姤鏈烘病鏈夎�呯數姹狅紝鏃犳硶浣跨敤",
          tip: "闇�瑕佸厛浠庢椂閽熸嬁鍒扮數姹�",
          type: "morse",
          data: {
            code: "...--/--.../.----",
            preClue: ["#鐢垫睜>鐢垫姤鏈�"]
          },
          state: [{
            name: "鐢垫姤鏈�",
            desc: "鐢垫姤鏈哄彂鍑轰簡鍝斿摂鍝旂殑澹板搷",
            tip: "鏍规嵁涔︽灦涓婄殑绗旇�板�圭収鎽╂柉瀵嗙爜寰楀埌 銆�371銆�",
            preClue: ["#鐢垫睜>鐢垫姤鏈�"]
          }]
        }]
      }, {
        name: "鏃堕挓",
        desc: "瀵归潰澧欎笂鐨勬椂閽熶技涔庡潖鎺変簡锛屼竴鐩村崱鍦ㄤ笁鐐瑰崐",
        nodes: [{
          name: "鐢垫睜",
          preClue: ["#閽ュ寵>闀ｉ搻"],
          interact: [{
            type: "use",
            target: "鐢垫姤鏈�",
            clue: "#鐢垫睜>鐢垫姤鏈�",
            audio: "浠�鍣ㄦ墦寮�",
            params: {
              isOnce: !0
            }
          }]
        }]
      }, {
        name: "鎺掓按绠�",
        desc: "杩炴帴鍦ㄥ�欓噷鐨勬帓姘寸�★紝浼间箮鍙�浠ョ敤宸ュ叿閿�鏂�",
        state: [{
          name: "妫嶅瓙",
          preClue: ["#妫嶅瓙"]
        }],
        interact: [{
          type: "use",
          target: "澧欎笂鐨勯挜鍖�",
          preClue: ["#妫嶅瓙"],
          clue: "#妫嶅瓙>澧欎笂鐨勯挜鍖�"
        }]
      }, {
        name: "涔︽灦",
        preClue: ["#閽ュ寵>闀ｉ搻"],
        nodes: [{
          name: "绗旇��",
          type: "image",
          data: {
            image: "images/morse.jpg"
          }
        }, {
          name: "鏃ヨ�版湰",
          nodes: [{
            name: "鏃ヨ�� 1",
            type: "text",
            data: {
              text: {
                content: `
<class='highlightTitle'>3鏈�12鏃�</class>

    浠婂ぉ鏃╀笂鎴戣捣搴婂悗锛屾垜浠庣獥澶栫湅鍒颁竴涓�濂囨��鐨勪汉锛屼粬涓�鐩寸洴鐫�鎴戣繖杈圭湅銆傛垜鏈変簺瀹虫�曪紝浜庢槸鎴戝叧涓婁簡绐楁埛銆�
    涓�鍗堢殑鏃跺�欙紝灏卞紑濮嬫敹鎷炬垜鐨勫ぇ閾佺�变簡銆傝繖涓�绠卞瓙鑳藉�熶繚瀛樻垜鎵�鏈夊績鐖辩殑涓滆タ銆傚墠浜涙棩瀛愯繕涓婁簡瀵嗙爜閿侊紝涓轰簡鎬曞繕璁版垜鎶婂瘑鐮佽�板埌鐢垫姤鏈洪噷锛岀劧鍚庡啀鍔犱笂鎴戠殑鐢熸棩锛屾垜澶�鑱�鏄庝簡銆傚搱鍝堛��
                      `
              }
            }
          }, {
            name: "鏃ヨ�� 2",
            type: "text",
            data: {
              text: {
                content: `
<class='highlightTitle'>3鏈�13鏃�</class>

    浠婂ぉ鎴戝幓璁�涓�鍧楃敓鏃ヨ泲绯曘�傛垜鍘讳簡闄勮繎鐨勯潰鍖呭簵锛屾寫閫変簡涓�鍧楀阀鍏嬪姏铔嬬硶銆傚簵鍛樺憡璇夋垜锛屾槑澶╀細灏嗚泲绯曢�佷笂闂�锛屾垜寰堟湡寰呫��
    鍦ㄥ洖瀹剁殑璺�涓婏紝鎴戝張娉ㄦ剰鍒颁簡閭ｄ釜鎬�浜恒�備粬涓�鐩磋窡鍦ㄦ垜鍚庨潰锛岃�╂垜鎰熷埌寰堜笉瀹夈�備簬鏄�鎴戝紑濮嬪姞蹇�姝ヤ紣锛岃瘯鍥炬憜鑴变粬鐨勮窡韪�銆傛渶缁堬紝鎴戝洖鍒颁簡瀹堕噷锛屾劅瑙夊ソ绱�銆�
                      `
              }
            }
          }, {
            name: "鏃ヨ�� 3",
            type: "text",
            data: {
              text: {
                content: `
<class='highlightTitle'>3鏈�14鏃�</class>

    鏃╀笂鏈変汉鏁查棬锛屾垜浠庣尗鐪肩湅娌℃湁浜猴紝涓嶇煡閬撴槸璋佸湪鏁查棬銆�
    鏄ㄥぉ璁㈢殑铔嬬硶涔熶竴鐩存病鏈夐�佽繃鏉ャ�傘�傘��
                      `
              }
            }
          }]
        }]
      }, {
        name: "澶ч搧绠�",
        preClue: ["#閽ュ寵>闀ｉ搻"],
        nodes: [{
          name: "瀵嗙爜閿�",
          tip: "鏍规嵁鎽╂柉瀵嗙爜鍜屾棩璁板緱鐭ョ殑鐢熸棩鐩稿姞寰楀埌 銆�685銆�",
          data: {
            lockClue: "#澶ч搧绠卞瘑鐮侀攣"
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
            clue: "#澶ч搧绠卞瘑鐮侀攣",
            preClue: ["#pass1-6", "#pass2-8", "#pass3-5"],
            params: {
              isOnce: !0
            }
          }]
        }, {
          name: "灏镐綋",
          desc: "涓�鍏峰案浣撹��閿佸湪閾佺�遍噷",
          preClue: ["#澶ч搧绠卞瘑鐮侀攣"],
          audio: "鎵撳紑閾侀棬",
          nodes: [{
            name: "鎵�",
            desc: "灏镐綋濉炲湪绠卞瓙閲屾棤娉曠Щ鍔�",
            tip: "鍥犱负灏镐綋鏃犳硶绉诲姩锛屾墍浠ラ渶瑕佸厛鐢ㄩ敮瀛愬緱鍒版墜鎸�",
            state: [{
              name: "鎵嬫寚",
              preClue: ["#鎵嬫寚"]
            }],
            interact: [{
              type: "use",
              target: "鎸囩汗閿�",
              clue: "#鎵嬫寚>鎸囩汗閿�",
              preClue: ["#鎵嬫寚"]
            }]
          }, {
            name: "鑴�",
            desc: "灏镐綋鑴镐笂鐨勮〃鎯呮儕鎭愬張鐥涜嫤"
          }]
        }]
      }, {
        name: "閿佺潃鐨勯棬",
        preClue: ["#閽ュ寵>闀ｉ搻"],
        state: [{
          name: "鍑哄彛",
          preClue: ["#鎵嬫寚>鎸囩汗閿�"]
        }],
        nodes: [{
          name: "鎸囩汗閿�",
          data: {
            lockClue: "#鎵嬫寚>鎸囩汗閿�"
          }
        }],
        interact: [{
          type: "click",
          clue: "@閫氬叧",
          preClue: ["#鎵嬫寚>鎸囩汗閿�"]
        }]
      }]
    }]
  }
  , Ii = {
    name: "mission3",
    missionName: "绗�涓夊叧",
    nextMission: "mission4",
    bgm: {
      闆烽洦: .5
    },
    nodes: [{
      point: "center",
      name: "瀹為獙瀹�",
      desc: "绌烘皵涓�寮ユ极鐫�涓�鑲″�囨��鐨勬皵鍛�",
      nodes: [{
        name: "閿佷綇鐨勯棬",
        desc: "鏃犳硶鎵撳紑锛岄渶瑕佸厛瑙ｉ櫎闂ㄧ�佺郴缁�",
        data: {
          lockClue: "#閿佷綇鐨勯棬"
        },
        state: [{
          name: "鍑哄彛",
          desc: "闂ㄥ凡缁忔墦寮�",
          preClue: "#閿佷綇鐨勯棬"
        }],
        interact: [{
          type: "click",
          clue: "@閫氬叧",
          preClue: "#閿佷綇鐨勯棬"
        }]
      }, {
        name: "閰嶇數绠�",
        state: [{
          name: "閰嶇數绠�",
          desc: "宸茬粡鎭㈠�嶇數鍔涗緵搴�",
          preClue: ["#鐢垫簮寮�鍏�"]
        }],
        nodes: [{
          name: "鐢垫簮寮�鍏�",
          tip: `鏍规嵁杩炵嚎璇存槑閲岀殑鍑哄叆鍙ｈ�掑害璋冩暣杩炵嚎瑙掑害
渚嬪�傞粍鑹插叆鍙ｅ拰鍑哄彛鏄� 180掳 鍚戜笅鐨刞,
          data: {
            noRefreshData: !0,
            lockClue: "#鐢垫簮寮�鍏�"
          },
          nodes: [{
            name: "钃濊壊杩炵嚎",
            type: "angle",
            data: {
              clue: "#blue-angle-{0}",
              precision: 30,
              lineColor: "#5271ff"
            }
          }, {
            name: "绾㈣壊杩炵嚎",
            type: "angle",
            data: {
              clue: "#red-angle-{0}",
              precision: 30,
              lineColor: "#ff3131"
            }
          }, {
            name: "榛勮壊杩炵嚎",
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
            clue: "#鐢垫簮寮�鍏�",
            audio: "鎭㈠�嶄緵鐢�",
            params: {
              isOnce: !0
            }
          }]
        }, {
          name: "杩炵嚎璇存槑",
          desc: "閰嶇數绠辩殑闂ㄨ儗闈㈣创鐫�涓�寮犵焊",
          type: "image",
          data: {
            image: "images/閰嶇數绠辫繛绾�.jpg"
          }
        }]
      }, {
        name: "瀹為獙鍙�",
        nodes: [{
          name: "鎺у埗缁堢��",
          desc: "娌℃湁鐢靛姏渚涘簲锛屾棤娉曚娇鐢�",
          state: [{
            name: "鎺у埗缁堢��",
            desc: "缁堢��杩炴帴鐫�涓�涓�鏁板瓧閿�鐩�",
            preClue: "#鐢垫簮寮�鍏�"
          }],
          nodes: [{
            name: "鎸夐挳",
            desc: "缁堢��鏄剧ず灞忎笂鍑虹幇浜� 銆�78963銆�",
            tip: "鎸夋暟瀛楀皬閿�鐩樼殑鎸夐敭杩炵嚎锛屾槸 銆�7銆�",
            preClue: "#鐢垫簮寮�鍏�",
            data: {
              activeColor: "#ffde59"
            }
          }, {
            name: "鎸夐挳",
            tip: "鎸夋暟瀛楀皬閿�鐩樼殑鎸夐敭杩炵嚎锛屾槸 銆�1銆�",
            preClue: "#鐢垫簮寮�鍏�",
            desc: "缁堢��鏄剧ず灞忎笂鍑虹幇浜� 銆�963銆�",
            data: {
              activeColor: "#ff3131"
            }
          }, {
            name: "鎸夐挳",
            tip: "鎸夋暟瀛楀皬閿�鐩樼殑鎸夐敭杩炵嚎锛屾槸 銆�4銆�",
            preClue: "#鐢垫簮寮�鍏�",
            desc: "缁堢��鏄剧ず灞忎笂鍑虹幇浜� 銆�7456963銆�",
            data: {
              activeColor: "#5271ff"
            }
          }],
          interact: [{
            type: "click",
            preClue: "#鍥惧舰璋滈��",
            clue: "#鎺у埗缁堢��"
          }]
        }, {
          name: "淇濋櫓鏌�",
          nodes: [{
            name: "瀵嗙爜閿�",
            data: {
              lockClue: "#淇濋櫓鏌�"
            },
            interact: [{
              type: "click",
              preClue: ["#yellow-7", "#red-1", "#blue-4"],
              clue: "#淇濋櫓鏌�",
              params: {
                isOnce: !0
              },
              audio: "瑙ｉ攣2"
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
            name: "瀹為獙鏃ヨ��",
            preClue: "#淇濋櫓鏌�",
            type: "image",
            data: {
              image: "images/瀹為獙鏃ヨ��1.jpg"
            },
            state: [{
              name: "瀹為獙鏃ヨ��",
              preClue: "#鐧界焊>绱�澶栫嚎鐏�",
              data: {
                image: "images/瀹為獙鏃ヨ��2.jpg"
              }
            }],
            interact: [{
              type: "use",
              target: "绱�澶栫嚎鐏�",
              clue: "#鐧界焊>绱�澶栫嚎鐏�"
            }]
          }, {
            name: "鎺㈡祴浠�",
            desc: "瓒婇潬杩戦噾灞烇紝闂�鐑侀�戠巼瓒婂揩",
            tip: "鎸�鍔ㄦ帰娴嬩华鑺傜偣锛屽０闊虫垨鐏�娉￠棯鐑佺殑棰戠巼瓒婂揩瓒婃帴杩戯紝鎵惧埌涓�涓�鐪嬩笉瑙佺殑銆岄殣钘忛棬銆嶈妭鐐�",
            preClue: "#淇濋櫓鏌�",
            type: "detector",
            data: {
              target: "闅愯棌闂�"
            },
            interact: [{
              type: "use",
              target: "闅愯棌闂�",
              clue: "#闅愯棌闂�",
              params: {
                isOnce: !0
              }
            }]
          }, {
            name: "闅愯棌闂�",
            key: "闅愯棌闂�",
            desc: "鐪嬭捣鏉ュ彧鏄�鏅�閫氱殑涓�闈㈠��",
            data: {
              noRefreshData: !0,
              independent: !0,
              stealthUntilClue: "#闅愯棌闂�",
              distance: Math.random() * 30 + 100
            },
            nodes: [{
              name: "瀵嗗��",
              preClue: "#闅愯棌闂�",
              audio: "鎵撳紑琛ｆ煖",
              interact: [{
                type: "click",
                clue: "#瀵嗗��"
              }],
              nodes: [{
                name: "绱�澶栫嚎鐏�",
                desc: "涓�鐩忕传澶栫嚎鐏�锛屼篃璁稿彲浠ョ敤鏉ョ収鍑洪殣钘忕殑绗旇抗"
              }, {
                name: "绁炵�樹华鍣�",
                desc: "妗屽瓙涓婃憜婊′簡鍚勭�嶇�炵�樼殑浠�鍣�",
                nodes: [{
                  name: "鑽�姘磋皟閰嶅櫒",
                  tip: "闇�瑕佸厛灏嗙传澶栫嚎鐏�鐓у皠瀹為獙鏃ヨ�帮紝鎵惧埌鐪熸�ｇ殑瑙ｈ嵂椤哄簭",
                  type: "color-sort",
                  data: {
                    colorCount: 4,
                    clue: "#鑽�姘磋皟閰�",
                    targetEntry: ["blue", "green", "red", "yellow"]
                  },
                  nodes: [{
                    name: "瑙ｈ嵂",
                    desc: "璋冮厤鍑烘潵鐨勮嵂鍓傦紝涔熻�告湁浠�涔堝姛鏁�",
                    audio: "鍙�",
                    interact: [{
                      type: "use",
                      target: "涓у案",
                      clue: "#瑙ｈ嵂",
                      params: {
                        isOnce: !0
                      }
                    }]
                  }]
                }, {
                  name: "鑽�绠�",
                  desc: "瑁呮弧鍚勭�嶉�滆壊鑽�鍓傜殑鑽�绠�",
                  audio: "闂�-寮�閿�",
                  nodes: [{
                    name: "绾㈣壊鑽�鍓�",
                    data: {
                      forColorSort: {
                        name: "鑽�姘磋皟閰嶅櫒",
                        color: "red",
                        entry: "red"
                      },
                      activeColor: "#ff3131"
                    }
                  }, {
                    name: "钃濊壊鑽�鍓�",
                    data: {
                      forColorSort: {
                        name: "鑽�姘磋皟閰嶅櫒",
                        color: "blue",
                        entry: "blue"
                      },
                      activeColor: "#5271ff"
                    }
                  }, {
                    name: "缁胯壊鑽�鍓�",
                    data: {
                      forColorSort: {
                        name: "鑽�姘磋皟閰嶅櫒",
                        color: "green",
                        entry: "green"
                      },
                      activeColor: "#609966"
                    }
                  }, {
                    name: "榛勮壊鑽�鍓�",
                    data: {
                      forColorSort: {
                        name: "鑽�姘磋皟閰嶅櫒",
                        color: "yellow",
                        entry: "yellow"
                      },
                      activeColor: "#ffde59"
                    }
                  }]
                }]
              }, {
                name: "涓у案",
                desc: "绌跨潃鐧藉ぇ瑜傜殑涓у案鎷峰湪瑙掕惤鍙戠媯锛屾棤娉曡交鏄撻潬杩�",
                audio: "涓у案",
                state: [{
                  name: "灏镐綋",
                  desc: "涓�鍏峰共鐦�鐨勫案浣�",
                  preClue: "#瑙ｈ嵂"
                }],
                nodes: [{
                  name: "鐧藉ぇ瑜�",
                  preClue: "#瑙ｈ嵂",
                  nodes: [{
                    name: "ID鍗�",
                    desc: "ID 鍗′笂鍐欑潃 銆屽疄楠屼汉鍛橈紝浜哄憳缂栧彿 996銆�",
                    interact: [{
                      type: "use",
                      target: "閿佷綇鐨勯棬",
                      clue: "#閿佷綇鐨勯棬"
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
    missionName: "绗�鍥涘叧",
    nextMission: "mission5",
    bgm: {
      椋�: .1,
      婊存按: 1
    },
    nodes: [{
      point: "center",
      name: "鐗㈡埧",
      desc: "鐏版殫鐨勭墷鎴匡紝鍥涘懆閮芥槸澧欏��",
      state: [],
      nodes: [{
        name: "澧欏��",
        desc: "涓婇潰鍒荤敾鐫�鍚勭�嶅浘妗堬紝鍏朵腑鍖呭惈鐫� 銆�1/3/2銆�",
        nodes: [{
          name: "瑁傜紳",
          desc: "澧欎笂鏈変竴閬撹�傜紳锛岄噷闈�浼间箮鏈変粈涔堜笢瑗�",
          type: "breakable",
          data: {
            clue: "#瑁傜紳",
            needInteractCount: 5,
            audio: "鍑�"
          },
          nodes: [{
            name: "閲戝竵",
            preClue: "#瑁傜紳",
            tip: "缁欎簣绁炵�樹汉鎹㈠彇鍑洪�冪殑鐗╁搧",
            audio: "閲戝竵鎺夎惤",
            interact: [{
              type: "use",
              target: "绁炵�樹汉",
              clue: "#閲戝竵>绁炵�樹汉",
              params: {
                isOnce: !0
              }
            }]
          }]
        }]
      }, {
        name: "閾佺獥",
        desc: "绔栫潃濂藉嚑鏍归搧妫嶇殑閾佺獥锛岃兘鏁插嚭娓呰剢鐨勫搷澹�",
        tip: "鏍规嵁澧欏�佺殑鎻愮ず锛屼緷娆℃暡鎵撻搧绐�1涓嬨��3涓嬨��2涓�",
        type: "knock",
        state: [{
          name: "閾佺獥",
          preClue: "#閾佺獥-1-3-2"
        }],
        data: {
          knockCount: 3,
          clue: "#閾佺獥-{0}-{1}-{2}",
          stopClue: "#閾佺獥-1-3-2",
          audio: "鏁查搧"
        },
        nodes: [{
          name: "閾佹��",
          preClue: "#閽冲瓙>閾佺獥",
          data: {
            autoAdd: !0
          },
          state: [{
            name: "閾佹��",
            desc: "閾佹�嶇殑涓�绔�鍚搁檮鐫�纾侀搧",
            preClue: "#纾侀搧>閾佹��"
          }],
          interact: [{
            type: "use",
            target: "鑰侀紶娲�",
            preClue: "#纾侀搧>閾佹��",
            clue: "#閾佹��>鑰侀紶娲�"
          }]
        }]
      }, {
        name: "绁炵�樹汉",
        desc: "鍑虹幇鍦ㄧ獥澶栫殑绁炵�樹汉",
        data: {
          noRefreshData: !0,
          independent: !0,
          stealthUntilClue: "#閾佺獥-1-3-2",
          removeIfClue: "#瀹濈煶>绁炵�樹汉",
          distance: 120
        },
        nodes: [{
          name: "閽冲瓙",
          preClue: "#閲戝竵>绁炵�樹汉",
          data: {
            autoAdd: !0,
            independent: !0
          },
          interact: [{
            type: "use",
            target: "閾佺獥",
            clue: "#閽冲瓙>閾佺獥",
            params: {
              isOnce: !0
            }
          }]
        }]
      }, {
        name: "閿佷綇鐨勭墷闂�",
        desc: "寰堝帤鐨勪竴鎵囩墷闂�锛屾渶搴曚笅鏈夎兘閫掍笢瑗跨殑缂哄彛",
        state: [{
          name: "鐗㈤棬",
          desc: "闇�瑕佺瓑寰呬竴瀹氱殑鏃舵満鎵嶈兘鍑洪��",
          preClue: "#閽ュ寵>鐗㈤棬"
        }],
        data: {
          lockClue: "#閽ュ寵>鐗㈤棬"
        },
        interact: [{
          type: "click",
          preClue: ["#閽ュ寵>鐗㈤棬", "#angle-60", "#angle-270"],
          clue: "@閫氬叧"
        }],
        nodes: [{
          name: "纾侀搧",
          desc: "鎺夎惤鍦ㄩ棬鏃佺殑纾侀搧锛屼篃璁告湁浠�涔堢敤",
          interact: [{
            type: "use",
            target: "閾佹��",
            clue: "#纾侀搧>閾佹��",
            params: {
              isOnce: !0
            }
          }]
        }, {
          name: "鐗㈤キ",
          preClue: "#瀹濈煶>绁炵�樹汉",
          audio: "閾佺洏婊戝姩",
          nodes: [{
            name: "閽ュ寵",
            desc: "钘忓湪鐗㈤キ閲岀殑閽ュ寵",
            interact: [{
              type: "use",
              target: "閿佷綇鐨勭墷闂�",
              clue: "#閽ュ寵>鐗㈤棬",
              params: {
                isOnce: !0
              }
            }]
          }, {
            name: "绾告潯",
            desc: "钘忓湪鐗㈤キ閲岀殑绾告潯锛屼笂闈㈠啓鐫� 銆�02:45銆�"
          }]
        }]
      }, {
        name: "鏈ㄥ簥",
        desc: "鍦颁笂鏀剧潃鐨勪竴寮犵牬鐮寸儌鐑傜殑鏈ㄥ簥",
        tip: "闇�瑕佹嬁鍒伴搧妫嶏紝鍐嶇敤閾佹�嶆暡鍑讳笁娆℃湪搴�",
        type: "breakable",
        data: {
          clue: "#鏈ㄥ簥",
          needInteractCount: 3,
          breakTarget: "閾佹��",
          audio: "鏁叉湪鏉�"
        },
        nodes: [{
          name: "閿佷綇鐨勯搧绠�",
          desc: "钘忓湪鏈ㄥ簥搴曚笅鐨勯搧绠憋紝闇�瑕侀挜鍖欐墠鑳芥墦寮�",
          preClue: "#鏈ㄥ簥",
          state: [{
            name: "閾佺��",
            preClue: "#閾佺�遍挜鍖�>閿佷綇鐨勯搧绠�"
          }],
          nodes: [{
            name: "瀹濈煶",
            desc: "涓�琚嬬拃鐠ㄧ殑瀹濈煶锛岃兘鍊煎緢澶氶挶",
            tip: "缁欎簣绁炵�樹汉鎹㈠彇鍑洪�冪殑鐗╁搧",
            preClue: "#閾佺�遍挜鍖�>閿佷綇鐨勯搧绠�",
            interact: [{
              type: "use",
              target: "绁炵�樹汉",
              clue: "#瀹濈煶>绁炵�樹汉",
              params: {
                isOnce: !0
              }
            }]
          }, {
            name: "鎬�琛�",
            preClue: "#閾佺�遍挜鍖�>閿佷綇鐨勯搧绠�",
            tip: "闇�瑕佸皢鎸囬拡璋冩暣鍒� 02:45 鐨勬柟鍚戞墠鑳芥墦寮�鐗㈡埧闂�",
            data: {
              noRefreshData: !0
            },
            nodes: [{
              name: "鏃堕拡",
              type: "angle",
              data: {
                clue: "#angle-{0}",
                precision: 30
              }
            }, {
              name: "鍒嗛拡",
              type: "angle",
              data: {
                clue: "#angle-{0}",
                precision: 30
              }
            }]
          }]
        }]
      }, {
        name: "鑰侀紶娲�",
        desc: "鍦颁笂鏈夎�侀紶娲烇紝鎵嬫棤娉曚几杩涘幓",
        tip: "闇�瑕佸甫纾侀搧鐨勯搧妫嶆墠鑳芥嬁鍒伴噷闈㈢殑涓滆タ",
        nodes: [{
          name: "閾佺�遍挜鍖�",
          preClue: "#閾佹��>鑰侀紶娲�",
          data: {
            autoAdd: !0
          },
          interact: [{
            type: "use",
            target: "閿佷綇鐨勯搧绠�",
            clue: "#閾佺�遍挜鍖�>閿佷綇鐨勯搧绠�",
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
    missionName: "绗�浜斿叧",
    nextMission: "mission6",
    cutscene: [{
      type: "text",
      desc: "鐐稿脊鐖嗙偢锛岄�冭劚澶辫触",
      preClue: "@澶辫触",
      time: 2e3,
      vibrate: "heavy"
    }],
    bgm: {},
    nodes: [{
      point: "center",
      name: "鎴块棿",
      desc: "鐪嬭捣鏉ユ槸鍙�鏈夌畝鍗曞嚑浠跺�跺叿鐨勪紤鎭�瀹�",
      nodes: [{
        name: "绐楁埛",
        desc: "鏃犳硶鎵撳紑鐨勭獥鎴凤紝澶�闃虫�ｅ湪缂撶紦钀戒笅"
      }, {
        name: "鍨冨溇妗�",
        nodes: [{
          name: "纰庣焊",
          type: "image",
          data: {
            image: "images/纰庣焊.png"
          }
        }]
      }, {
        name: "鐐稿脊",
        desc: "缁撳疄鐨勫啗鐏�绠憋紝涓�闂寸殑鐜荤拑鑳界湅鍒扮偢寮瑰�掕�℃椂",
        type: "timer",
        data: {
          time: 60 * 5,
          stopClue: "#瑙ｉ櫎鐐稿脊",
          overClue: "@澶辫触",
          effectAudio: "bomb-di",
          overAudio: "bomb-boom"
        },
        nodes: [{
          name: "閿佷綇鐨勫啗鐏�绠�",
          desc: "閿佷綇浜嗭紝闇�瑕侀挜鍖欐墠鑳芥墦寮�",
          data: {
            lockClue: "#鍐涚伀绠遍挜鍖�>閿佷綇鐨勫啗鐏�绠�"
          },
          state: [{
            name: "鍐涚伀绠�",
            preClue: "#鍐涚伀绠遍挜鍖�>閿佷綇鐨勫啗鐏�绠�"
          }],
          nodes: [{
            name: "寮曠垎瑁呯疆",
            desc: "鍦ㄨВ闄ょ偢寮瑰墠锛屾渶濂戒笉瑕佸幓鎷嗗畠",
            state: [{
              name: "寮曠垎瑁呯疆",
              desc: "涓�闂村祵鐫�鏌卞舰閽ュ寵锛屼技涔庤兘鎼炰笅鏉�",
              preClue: "#瑙ｉ櫎鐐稿脊"
            }],
            preClue: ["#鍐涚伀绠遍挜鍖�>閿佷綇鐨勫啗鐏�绠�"],
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
              name: "鏌卞舰閽ュ寵",
              preClue: ["#铻轰笣鍒�>寮曠垎瑁呯疆"],
              data: {
                autoAdd: !0
              },
              interact: [{
                type: "use",
                target: "涔︽灦",
                clue: "#鏌卞舰閽ュ寵>涔︽灦",
                params: {
                  isOnce: !0
                }
              }]
            }],
            interact: [{
              type: "click",
              clue: "#瑙ｉ櫎鐐稿脊",
              preClue: ["#pass1-4", "#pass2-3", "#pass3-1"]
            }]
          }]
        }]
      }, {
        name: "妗屽瓙",
        desc: "涓�涓�鏈ㄨ川鐨勫姙鍏�妗�",
        nodes: [{
          name: "鐢佃剳",
          nodes: [{
            name: "寮�鏈哄瘑鐮�",
            tip: "鏍规嵁鍨冨溇妗剁殑纰庣焊鎻愮ず瀵嗙爜涓虹孩2榛�3钃�9",
            data: {
              lockClue: "#寮�鏈哄瘑鐮�"
            },
            interact: [{
              type: "click",
              preClue: ["#yellow-3", "#red-2", "#blue-9"],
              clue: "#寮�鏈哄瘑鐮�",
              params: {
                isOnce: !0
              },
              audio: "寮�鏈�"
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
            name: "閭�绠�",
            preClue: "#寮�鏈哄瘑鐮�",
            nodes: [{
              name: "閭�浠�1",
              type: "text",
              data: {
                text: {
                  title: "鎸囩ず閭�浠�",
                  content: `
鎴戜滑鐨勭�樺瘑鍩哄湴宸茶��鍙戠幇锛岀珛鍗充娇鐢ㄧ偢寮圭偢姣佹�ゅ�勶紝骞朵笖鎽ф瘉鍐呴儴鏁版嵁鏂囦欢銆�
                          `
                }
              }
            }, {
              name: "閭�浠�2",
              type: "text",
              data: {
                text: {
                  title: "鐐稿脊璇存槑",
                  content: `
<class='highlight'>鐐稿脊瀹夎�咃細</class>
1. 缁勭粐鍐呴儴鐨勬煴褰㈤挜鍖欐斁鍏ュ紩鐖嗚�呯疆
2. 瑁呬笂鐩栨澘
3. 杈撳叆琛屽姩浠ｅ彿
4. 璁惧畾鍊掕�℃椂鍚�鍔ㄧ偢寮�

<class='highlight'>鐐稿脊瑙ｉ櫎锛�</class>
灏嗚�屽姩浠ｅ彿鍙嶈浆鍚庤緭鍏ュ嵆鍙�瑙ｉ櫎锛屽垏璁版敹鍒拌�屽姩浠ｅ彿鍚庣珛鍗抽攢姣侀偖浠躲��
                          `
                }
              }
            }, {
              name: "閭�浠�3",
              type: "text",
              data: {
                text: {
                  title: "琛屽姩浠ｅ彿",
                  content: `
<class='remark'>-- 鍐呭�瑰凡閿�姣� --</class>
                          `
                }
              }
            }]
          }, {
            name: "鍔犲瘑鏂囦欢",
            preClue: "#寮�鏈哄瘑鐮�",
            desc: "鏂囦欢鍐呭�瑰凡琚�鍔犲瘑锛岄渶瑕佸瘑閽ヨВ瀵�",
            state: [{
              name: "鏁版嵁鏂囦欢",
              desc: "閭�鎭剁粍缁囩殑閲嶈�佹暟鎹�鏂囦欢",
              preClue: ["#瀵嗛挜>鍔犲瘑鏂囦欢"]
            }],
            type: "text",
            data: {
              lockClue: "#鍔犲瘑鏂囦欢",
              preClue: ["#瀵嗛挜>鍔犲瘑鏂囦欢"],
              text: {
                title: "缁勭粐鍐呴儴鏂囦欢",
                content: `
<class='highlight'>琛屽姩璁″垝锛�</class>

浠ｅ彿134锛�
> 鍦ㄥ熀鍦� 6 灞傚崡杈圭殑浼戞伅瀹ゅ畨缃�鐐稿脊
> 浼戞伅瀹ゅ瘑鐮佷负鎴块棿鍙�

<class='remark'>-- 鐪佺暐鍏朵粬璁″垝 --</class>

浜哄憳鍚嶅崟锛�

<class='remark'>-- 鐪佺暐 --</class>
                      `
              }
            }
          }]
        }, {
          name: "渚跨��",
          tip: "浣跨敤閾呯瑪鍙�浠ユ壘鍒拌�屽姩浠ｅ彿鐥曡抗",
          desc: "涓�娌撲究绛撅紝宸茬粡琚�鎾曟帀浜嗕竴浜�",
          state: [{
            name: "渚跨��",
            desc: "鐢ㄩ搮绗旀秱浜嗗悗锛岃兘鐪嬪埌鍐欒繃 銆屼唬鍙�134銆� 鐨勭棔杩�",
            preClue: ["#閾呯瑪>渚跨��"]
          }]
        }, {
          name: "鎶藉眽",
          nodes: [{
            name: "铻轰笣鍒�",
            interact: [{
              type: "use",
              target: "寮曠垎瑁呯疆",
              preClue: ["#瑙ｉ櫎鐐稿脊"],
              clue: "#铻轰笣鍒�>寮曠垎瑁呯疆"
            }, {
              type: "use",
              target: "閫氶�庡彛",
              clue: "#铻轰笣鍒�>閫氶�庡彛"
            }]
          }, {
            name: "閾呯瑪",
            interact: [{
              type: "use",
              target: "渚跨��",
              clue: "#閾呯瑪>渚跨��",
              desc: "鐢ㄩ搮绗旀秱浜嗗悗锛岃兘鐪嬪埌鍐欒繃 銆屼唬鍙�134銆� 鐨勭棔杩�"
            }]
          }]
        }]
      }, {
        name: "閫氶�庡彛",
        tip: "鍙�浠ヤ娇鐢ㄨ灪涓濆垁鎵撳紑閫氶�庡彛",
        desc: "涓�涓�涓嶅ぇ鐨勯�氶�庡彛锛岃��鐧惧彾绐楃洊浣忎簡",
        state: [{
          name: "閫氶�庡彛",
          desc: "鐧惧彾绐楀凡缁忔墦寮�浜�",
          preClue: ["#铻轰笣鍒�>閫氶�庡彛"]
        }],
        nodes: [{
          name: "鍐涚伀绠遍挜鍖�",
          preClue: ["#铻轰笣鍒�>閫氶�庡彛"],
          interact: [{
            type: "use",
            target: "閿佷綇鐨勫啗鐏�绠�",
            clue: "#鍐涚伀绠遍挜鍖�>閿佷綇鐨勫啗鐏�绠�",
            params: {
              isOnce: !0
            }
          }]
        }]
      }, {
        name: "閿佷綇鐨勯棬",
        desc: "鏃犳硶鎵撳紑锛岄渶瑕佸厛瑙ｉ櫎闂ㄧ�佺郴缁�",
        data: {
          lockClue: "#閿佷綇鐨勯棬"
        },
        state: [{
          name: "鍑哄彛",
          desc: "闂ㄥ凡缁忔墦寮�",
          preClue: "#閿佷綇鐨勯棬"
        }],
        interact: [{
          type: "click",
          clue: "@閫氬叧",
          preClue: "#閿佷綇鐨勯棬"
        }],
        nodes: [{
          name: "闂ㄧ�佸瘑鐮�",
          tip: "鏍规嵁绐楁埛鑳界湅鍒拌惤鏃ュ緱鐭ョ獥鎴锋湞瑗匡紝鍐嶆牴鎹�骞抽潰鍥句笌鍐呴儴鏂囦欢寰楃煡瀵嗙爜涓� 605",
          preClue: ["#ID鍗�>閿佷綇鐨勯棬"],
          data: {
            lockClue: "#閿佷綇鐨勯棬"
          },
          nodes: [{
            name: "0",
            type: "password",
            data: {
              text: "1",
              clue: "#闂ㄧ�佸瘑鐮�1-{0}"
            }
          }, {
            name: "0",
            type: "password",
            data: {
              text: "2",
              clue: "#闂ㄧ�佸瘑鐮�2-{0}"
            }
          }, {
            name: "0",
            type: "password",
            data: {
              text: "3",
              clue: "#闂ㄧ�佸瘑鐮�3-{0}"
            }
          }],
          interact: [{
            type: "click",
            preClue: ["#闂ㄧ�佸瘑鐮�1-6", "#闂ㄧ�佸瘑鐮�2-0", "#闂ㄧ�佸瘑鐮�3-5"],
            clue: "#閿佷綇鐨勯棬",
            params: {
              isOnce: !0
            }
          }]
        }]
      }, {
        name: "涔︽灦",
        desc: "鏀剧潃寰堝�氫功鐨勪功鏋讹紝鍏朵腑涓ゆ湰涔︿腑闂存湁涓�濂囨��鐨勫叚杈瑰舰娲�",
        nodes: [{
          name: "銆婄�炵�樼櫨鎱曞ぇ銆�",
          desc: "灏侀潰涓婂啓鐫� 銆孉25-B5-C5銆�"
        }, {
          name: "銆婄悆褰㈤棯鐢点��",
          desc: "灏侀潰涓婂啓鐫� 銆孉5-B5-C5-D2銆�"
        }, {
          name: "銆婃槦闄呰糠鑸�銆�",
          desc: "灏侀潰涓婂啓鐫� 銆孉245-B5-C5銆�"
        }, {
          name: "鏆楀��",
          desc: "鎻掑叆鏌卞舰閽ュ寵鍚庯紝涔︽灦绉诲姩鍑虹幇浜嗘殫瀹�",
          preClue: ["#鏌卞舰閽ュ寵>涔︽灦"],
          nodes: [{
            name: "娴锋姤",
            desc: "璐村湪澧欎笂鐨勫�囨��娴锋姤",
            tip: "鏍规嵁涔︽灦涓婄殑涔﹀垎鍒�濉�鍏ュ緱鍒板�瑰簲瀵嗙爜",
            type: "image",
            data: {
              image: "images/mission5-post.jpg"
            }
          }, {
            name: "妤煎眰骞抽潰鍥�",
            desc: "璐村湪闂ㄤ笂鐨勬ゼ灞傚钩闈㈠浘",
            type: "image",
            data: {
              image: "images/mission5-floor.jpg"
            }
          }, {
            name: "淇濋櫓鏌�",
            nodes: [{
              name: "瀵嗙爜閿�",
              tip: "涔﹀悕瀵瑰簲鐫�鍥惧舰锛屻�婄�炵�樼櫨鎱曞ぇ銆嬩唬琛ㄤ笁瑙掑舰锛屻�婄悆褰㈤棯鐢点�嬩唬琛ㄥ渾褰�锛屻�婃槦闄呯┛瓒娿�嬩唬琛ㄤ簲瑙掓槦",
              data: {
                lockClue: "#淇濋櫓鏌滃瘑鐮侀攣"
              },
              nodes: [{
                name: "0",
                type: "password",
                data: {
                  text: "鈻�",
                  clue: "#淇濋櫓鏌�1-{0}"
                }
              }, {
                name: "0",
                type: "password",
                data: {
                  text: "鈼�",
                  clue: "#淇濋櫓鏌�2-{0}"
                }
              }, {
                name: "0",
                type: "password",
                data: {
                  text: "鈽�",
                  clue: "#淇濋櫓鏌�3-{0}"
                }
              }],
              interact: [{
                type: "click",
                preClue: ["#淇濋櫓鏌�1-5", "#淇濋櫓鏌�2-3", "#淇濋櫓鏌�3-6"],
                clue: "#淇濋櫓鏌滃瘑鐮侀攣",
                params: {
                  isOnce: !0
                }
              }]
            }, {
              name: "瀵嗛挜",
              desc: "涓�澶т覆澶嶆潅鐨勫瘑閽�",
              preClue: ["#淇濋櫓鏌滃瘑鐮侀攣"],
              interact: [{
                type: "use",
                target: "鍔犲瘑鏂囦欢",
                clue: "#瀵嗛挜>鍔犲瘑鏂囦欢",
                params: {
                  isOnce: !0
                }
              }]
            }, {
              name: "ID鍗�",
              preClue: ["#淇濋櫓鏌滃瘑鐮侀攣"],
              interact: [{
                type: "use",
                target: "閿佷綇鐨勯棬",
                clue: "#ID鍗�>閿佷綇鐨勯棬"
              }]
            }]
          }]
        }]
      }]
    }]
  }
  , Ui = {
    name: "mission6",
    missionName: "绗�鍏�鍏�",
    nextMission: "mission7",
    bgm: {
      鍦颁笅婊存按: .8
    },
    nodes: [{
      point: "center",
      name: "鍦颁笅瀹�",
      desc: "鏄忔殫鐨勫湴涓嬪�わ紝澶撮《鐨勭伅娉″湪闂�鐑佺潃寰�寮辩殑鍏�",
      nodes: [{
        name: "閿佷綇鐨勯棬",
        desc: "閫氬線鍦伴潰鐨勯棬锛岄攣浣忎簡鏃犳硶鎵撳紑",
        data: {
          lockClue: "#閿佷綇鐨勯棬"
        },
        state: [{
          name: "鍑哄彛",
          preClue: ["#閿佷綇鐨勯棬"]
        }],
        nodes: [{
          name: "瀵嗙爜閿�",
          data: {
            lockClue: "#閿佷綇鐨勯棬"
          },
          nodes: [{
            name: "0",
            type: "password",
            data: {
              text: "1",
              clue: "#閿佷綇鐨勯棬1-{0}"
            }
          }, {
            name: "0",
            type: "password",
            data: {
              text: "2",
              clue: "#閿佷綇鐨勯棬2-{0}"
            }
          }, {
            name: "0",
            type: "password",
            data: {
              text: "3",
              clue: "#閿佷綇鐨勯棬3-{0}"
            }
          }],
          interact: [{
            type: "click",
            preClue: ["#閿佷綇鐨勯棬1-4", "#閿佷綇鐨勯棬2-1", "#閿佷綇鐨勯棬3-9"],
            clue: "#閿佷綇鐨勯棬",
            params: {
              isOnce: !0
            }
          }]
        }],
        interact: [{
          type: "click",
          clue: "@閫氬叧",
          preClue: "#閿佷綇鐨勯棬"
        }]
      }, {
        name: "妗屽瓙",
        desc: "涓�寮犵牬鏃х殑鏈ㄦ��",
        nodes: [{
          name: "绌洪厭鐡�",
          desc: "鏁ｈ惤鍦ㄦ�屼笂鐨勭┖閰掔摱",
          state: [{
            name: "瑁呮弧姘寸殑閰掔摱",
            preClue: "#瑁呮弧姘寸殑閰掔摱"
          }],
          interact: [{
            type: "use",
            target: "鎺掓按鍙�",
            clue: "#瑁呮弧姘寸殑閰掔摱>鎺掓按鍙�",
            preClue: ["#瑁呮弧姘寸殑閰掔摱"]
          }]
        }, {
          name: "绗旇�版湰鐢佃剳",
          desc: "浼间箮鏄�鎴戝甫鏉ョ殑绗旇�版湰鐢佃剳锛屼絾鏄�宸茬粡娌＄數浜�",
          state: [{
            name: "绗旇�版湰鐢佃剳",
            preClue: ["#鐢垫簮绾�>绗旇�版湰鐢佃剳"]
          }],
          nodes: [{
            name: "閿�鐩�",
            tip: "鏈夐厭绮剧殑鍛抽亾浠ｈ〃鏈変汉鍠濋厭骞舵妸閰掑紕鍦ㄤ簡閿�鐩樹笂锛屽姞鑽�鍝佺矇鏈�鑳界湅鍒版寜閿�鐥曡抗",
            desc: "鑴忓叜鍏�鐨勯敭鐩橈紝涓婇潰鏈変竴鑲￠厭绮剧殑鍛抽亾",
            state: [{
              name: "閿�鐩�",
              desc: "娲掍笂绮夋湯鍚庡惞鎺夛紝0銆�2銆�7 鎸夐敭浠嶆畫鐣欑矇鏈�",
              preClue: "#鑽�鍝�>閿�鐩�"
            }]
          }, {
            name: "寮�鏈哄瘑鐮�",
            tip: "鏍规嵁閿�鐩樻彁绀哄緱鍒� 0銆�2銆�7 涓変釜鏁板瓧锛屽啀鏍规嵁寮�鏈哄瘑鐮佹彁绀哄彲鐭ュ瘑鐮佷负 702",
            preClue: "#鐢垫簮绾�>绗旇�版湰鐢佃剳",
            desc: "瀵嗙爜鎻愮ず锛氫笉琚� 5 鏁撮櫎鐨勪笁浣嶆暟鐨勫伓鏁�",
            data: {
              lockClue: "#寮�鏈哄瘑鐮�"
            },
            nodes: [{
              name: "0",
              type: "password",
              data: {
                text: "1",
                clue: "#寮�鏈哄瘑鐮�1-{0}"
              }
            }, {
              name: "0",
              type: "password",
              data: {
                text: "2",
                clue: "#寮�鏈哄瘑鐮�2-{0}"
              }
            }, {
              name: "0",
              type: "password",
              data: {
                text: "3",
                clue: "#寮�鏈哄瘑鐮�3-{0}"
              }
            }],
            interact: [{
              type: "click",
              preClue: ["#寮�鏈哄瘑鐮�1-7", "#寮�鏈哄瘑鐮�2-0", "#寮�鏈哄瘑鐮�3-2"],
              clue: "#寮�鏈哄瘑鐮�",
              audio: "寮�鏈�",
              params: {
                isOnce: !0
              }
            }]
          }, {
            name: "宸查攢姣佺殑鏁版嵁",
            desc: "鐪嬭捣鏉ユ暟鎹�宸茬粡琚�閿�姣佷簡锛屾棤娉曚娇鐢�",
            preClue: ["#鐢垫簮绾�>绗旇�版湰鐢佃剳", "#寮�鏈哄瘑鐮�"]
          }, {
            name: "鍐呴儴鏁版嵁",
            desc: "鏁版嵁閲忓簽澶х殑缁勭粐鍐呴儴鏁版嵁锛屼笉妫�绱㈠緢闅炬壘鍒版湁鐢ㄧ殑淇℃伅",
            preClue: ["#鐢垫簮绾�>绗旇�版湰鐢佃剳", "#寮�鏈哄瘑鐮�", "#U鐩�>绗旇�版湰鐢佃剳"],
            nodes: [{
              name: "妫�绱�",
              tip: "鏍规嵁琛屽姩鎸囦护妫�绱�浜哄憳缂栧彿 138 寰楀埌姝や汉璧勬枡",
              nodes: [{
                name: "0",
                type: "password",
                data: {
                  text: "1",
                  clue: "#妫�绱�1-{0}"
                }
              }, {
                name: "0",
                type: "password",
                data: {
                  text: "2",
                  clue: "#妫�绱�2-{0}"
                }
              }, {
                name: "0",
                type: "password",
                data: {
                  text: "3",
                  clue: "#妫�绱�3-{0}"
                }
              }],
              interact: [{
                type: "click",
                preClue: ["#妫�绱�1-1", "#妫�绱�2-3", "#妫�绱�3-8"],
                clue: "#妫�绱�138"
              }, {
                type: "click",
                preClue: ["#妫�绱�1-4", "#妫�绱�2-4", "#妫�绱�3-4"],
                clue: "#妫�绱�444"
              }, {
                type: "click",
                preClue: ["#妫�绱�1-9", "#妫�绱�2-9", "#妫�绱�3-6"],
                clue: ["#妫�绱�996", "%mission6-996"]
              }]
            }, {
              name: "缂栧彿 138 璧勬枡",
              preClue: ["#妫�绱�138"],
              type: "text",
              data: {
                text: {
                  title: "浜哄憳缂栧彿138",
                  content: `
鐩村睘浜庣紪鍙� 444 鐨勬墽琛屼汉鍛橈紝璐熻矗鎵ц�岄摬闄ゃ�佺垎鐮淬�侀攢姣佽瘉鎹�绛変换鍔°��
                          `
                }
              }
            }, {
              name: "缂栧彿 444 璧勬枡",
              preClue: ["#妫�绱�444"],
              type: "text",
              data: {
                text: {
                  title: "浜哄憳缂栧彿444",
                  content: `
鎵撳叆鐗瑰伐鏈烘瀯鐨勯珮绾т汉鍛橈紝鍦ㄧ壒宸ユ満鏋勫寲鍚� DD锛岃礋璐ｈ幏鍙栫壒宸ユ満鏋勭殑鍗у簳淇℃伅锛屽�圭粍缁囨湁瀹崇殑鐗瑰伐杩涜�岄摬闄ゃ��

浣忓�勶細AA 甯傚尯 BB 璺� 419 鍙� XX 灞卞簞銆�
                          `
                }
              }
            }, {
              name: "缂栧彿 996 璧勬枡",
              preClue: ["#妫�绱�996"],
              type: "text",
              data: {
                text: {
                  title: "浜哄憳缂栧彿996",
                  content: `
楂樼骇瀹為獙浜哄憳锛岃礋璐ｇ爺鍙戜汉浣撳彉寮傜殑鐢熷寲姝﹀櫒銆�

鐩�鍓嶄汉鍛樹笅钀戒笉鏄庯紝瀹為獙璧勬枡涓㈠け锛岃�″垝缁堟��銆�
                          `
                }
              }
            }]
          }]
        }]
      }, {
        name: "宸ヤ綔鍙�",
        nodes: [{
          name: "姘撮緳澶�",
          interact: [{
            type: "use",
            target: "绌洪厭鐡�",
            clue: "#瑁呮弧姘寸殑閰掔摱"
          }]
        }, {
          name: "鑽�鍝�",
          desc: "涓�绉嶇矇鏈�鐘剁殑鑽�鍝侊紝涓婇潰鍐欑潃鑳藉�硅�板繂杩涜�屾竻闄�",
          interact: [{
            type: "use",
            target: "閿�鐩�",
            clue: "#鑽�鍝�>閿�鐩�"
          }]
        }, {
          name: "閾佺洅",
          desc: "涓�涓�缁撳疄鐨勯搧鐩掞紝涓婇潰鐢ㄥ瘑鐮侀攣閿佺潃",
          nodes: [{
            name: "瀵嗙爜閿�",
            data: {
              lockClue: "#瀵嗙爜閿�"
            },
            nodes: [{
              name: "0",
              type: "password",
              data: {
                text: "鈻�",
                clue: "#瀵嗙爜閿�3-{0}"
              }
            }, {
              name: "0",
              type: "password",
              data: {
                text: "鈼�",
                clue: "#瀵嗙爜閿�0-{0}"
              }
            }, {
              name: "0",
              type: "password",
              data: {
                text: "鈻�",
                clue: "#瀵嗙爜閿�4-{0}"
              }
            }],
            interact: [{
              type: "click",
              preClue: ["#瀵嗙爜閿�3-5", "#瀵嗙爜閿�4-2", "#瀵嗙爜閿�0-3"],
              clue: "#瀵嗙爜閿�",
              params: {
                isOnce: !0
              }
            }]
          }, {
            name: "鐢垫簮绾�",
            preClue: "#瀵嗙爜閿�",
            desc: "涓�鏍圭數婧愮嚎锛岀湅璧锋潵鏄�鐢ㄦ潵缁欑數鑴戜緵鐢电殑",
            interact: [{
              type: "use",
              target: "绗旇�版湰鐢佃剳",
              clue: "#鐢垫簮绾�>绗旇�版湰鐢佃剳",
              params: {
                isOnce: !0
              }
            }]
          }, {
            name: "涓�浜烘。妗�",
            tip: "鐢熸棩 512 鏄�鎵嬫満鐨勯攣灞忓瘑鐮�",
            desc: "妗ｆ�堜笂闈㈣创鐫�鎴戠殑鐓х墖锛屼技涔庢槸鎴戠殑妗ｆ��",
            preClue: "#瀵嗙爜閿�",
            type: "text",
            data: {
              text: {
                title: "涓�浜烘。妗�",
                content: `
濮撳悕锛氬紶浼�
鎬у埆锛氱敺
鍑虹敓鏃ユ湡锛�1992骞�5鏈�12鏃�
韬�浠斤細鐗瑰伐
                      `
              }
            }
          }, {
            name: "琛屽姩鎸囦护",
            tip: "缂栧彿 138 涓哄唴閮ㄦ暟鎹�妫�绱㈡椂浣跨敤",
            preClue: "#瀵嗙爜閿�",
            type: "text",
            data: {
              text: {
                title: "琛屽姩鎸囦护",
                content: `
涓婃�＄殑鐖嗙偢琛屽姩璁″垝鏈�鑳芥垚鍔熼摬闄ゆ�や汉锛岃繕璁╀粬鑾峰彇缁勭粐鐨勫唴閮ㄦ暟鎹�銆�

鎴戝皢浼氬畨鎺掓�や汉鍒� XX 灞卞簞浜ゆ帴鏁版嵁锛屼綘鎶婁粬鎵撴檿鍚庡叧鍏ュ湴涓嬪�わ紝骞跺皢鏁版嵁鍏ㄩ儴閿�姣佹帀銆�(鍦颁笅瀹ゅ瘑鐮佷负闂ㄧ墝鍙�)

涓婂眰宸查珮搴﹂噸瑙嗘�や汉锛屼笉瑕佺洿鎺ユ潃鎺夛紝鍏堢敤绉樺瘑鑽�鐗╁幓鎺変粬鐨勮�板繂锛岀‘淇濆�圭粍缁囨棤瀹冲悗鍐嶆斁鍑恒��
                      `,
                name: "To 缂栧彿138"
              }
            }
          }]
        }]
      }, {
        name: "鎺掓按鍙�",
        tip: "浣跨敤鎵嬫満鑳界湅鍒伴噷闈㈡湁涓滆タ锛岀┖閰掔摱鐢ㄦ按榫欏ご瑁呮按鍚庡�掑叆鍗冲彲",
        desc: "涓�涓�灏忓皬娲炲彛鐨勬帓姘村彛锛岀湅涓嶆竻閲岄潰鏈変粈涔�",
        state: [{
          name: "鎺掓按鍙�",
          desc: "鐪嬭捣鏉ユ槸鍫垫�荤殑鎺掓按鍙ｏ紝搴曢儴鏈変粈涔堜笢瑗�",
          preClue: "#鎵嬫満>鎺掓按鍙�"
        }, {
          name: "鎺掓按鍙�",
          preClue: "#瑁呮弧姘寸殑閰掔摱>鎺掓按鍙�"
        }],
        nodes: [{
          name: "绾稿洟",
          desc: "浠庢帓姘村彛娴�涓婃潵鐨勭焊鍥�",
          preClue: "#瑁呮弧姘寸殑閰掔摱>鎺掓按鍙�",
          state: [{
            name: "绾告潯",
            tip: "绗�涓�涓�鏁板瓧浠ｈ〃瑙掔殑鏁伴噺锛岀��浜屼釜鏁板瓧浠ｈ〃瀵瑰簲瀵嗙爜銆備緥濡� 35 浠ｈ〃涓夎�掑舰鐨勫瘑鐮佷负 5銆�",
            desc: "鐨卞反宸寸殑绾告潯涓婂啓鐫� 銆�35-42-03銆�",
            preClue: "#绾告潯"
          }],
          interact: [{
            type: "click",
            clue: "#绾告潯",
            desc: "鐨卞反宸寸殑绾告潯涓婂啓鐫� 銆�35-42-03銆�"
          }]
        }]
      }, {
        name: "鑳屽寘",
        desc: "闈犲湪澧欒竟鐨勮儗鍖咃紝浼间箮鏄�鎴戠殑",
        nodes: [{
          name: "鎵嬫満",
          desc: "涓�閮ㄦ櫤鑳芥墜鏈猴紝澹佺焊涓婄殑浜烘槸鎴戣嚜宸便�傛墜鏈烘病鏈変俊鍙�",
          nodes: [{
            name: "閿佸睆瀵嗙爜",
            tip: "鍥犱负鏄�鎴戠殑鎵嬫満锛屽悗缁�寰楀埌涓�浜烘。妗堝悗杈撳叆鐢熸棩鍗冲彲",
            desc: "鍥犱负澶卞繂璁颁笉璧锋潵閿佸睆瀵嗙爜浜�",
            data: {
              lockClue: "#閿佸睆瀵嗙爜"
            },
            nodes: [{
              name: "0",
              type: "password",
              data: {
                text: "1",
                clue: "#閿佸睆瀵嗙爜1-{0}"
              }
            }, {
              name: "0",
              type: "password",
              data: {
                text: "2",
                clue: "#閿佸睆瀵嗙爜2-{0}"
              }
            }, {
              name: "0",
              type: "password",
              data: {
                text: "3",
                clue: "#閿佸睆瀵嗙爜3-{0}"
              }
            }],
            interact: [{
              type: "click",
              preClue: ["#閿佸睆瀵嗙爜1-5", "#閿佸睆瀵嗙爜2-1", "#閿佸睆瀵嗙爜3-2"],
              clue: "#閿佸睆瀵嗙爜",
              params: {
                isOnce: !0
              }
            }]
          }, {
            name: "鐭�淇�",
            preClue: "#閿佸睆瀵嗙爜",
            nodes: [{
              name: "鍙戦�佺煭淇�1",
              type: "text",
              data: {
                text: {
                  title: "鍙戦�佺煭淇�",
                  content: `
鎴戝凡鐮磋В浜嗕粬浠�鐨勭偢寮硅�″垝锛屽苟涓旇幏鍙栦簡閭�鎭剁粍缁囩殑鍐呴儴璧勬枡銆�
                          `
                }
              }
            }, {
              name: "鎺ユ敹鐭�淇�2",
              type: "text",
              data: {
                text: {
                  title: "鎺ユ敹鐭�淇�",
                  content: `
濂界殑銆傝�蜂簬鏄庢棭鍒� XX 灞卞簞浜ゆ帴鏁版嵁銆�

鍒囪�板洜鏁版嵁娑夊強鍥藉�跺畨鍏�锛屼笉寰楁硠闇蹭篃涓嶅彲绉佽嚜鏌ョ湅銆�
                          `,
                  name: "From DD"
                }
              }
            }]
          }, {
            name: "澶囧繕褰�",
            tip: "鐪嬪畬澶囧繕褰曞悗鍐嶇偣鍑绘墦鐏�鏈轰細鍑虹幇鏆楁牸锛屽啀杩炵偣 3 娆℃殫鏍煎嵆鍙�鑾峰緱 U 鐩�",
            preClue: "#閿佸睆瀵嗙爜",
            type: "text",
            data: {
              text: {
                title: "澶囧繕褰�",
                content: `
鎴戞湁涓�澶栬�傜湅璧锋潵鏄�鎵撶伀鏈猴紝瀹為檯涓婂簳閮ㄦ湁涓�鏆楁牸锛屽彧闇�瑕佽繛鎸変笁娆″氨浼氬脊鍑� U 鐩樸��

浠ラ槻涓囦竴锛屾垜灏嗘暟鎹�澶囦唤鍒颁簡 U 鐩樹腑銆�
                      `
              }
            },
            interact: [{
              type: "click",
              clue: "#澶囧繕褰�"
            }]
          }],
          interact: [{
            type: "use",
            target: "鎺掓按鍙�",
            clue: "#鎵嬫満>鎺掓按鍙�"
          }]
        }, {
          name: "鎵撶伀鏈�",
          desc: "涓�涓�鍧忔帀鐨勯搧鍒舵墦鐏�鏈猴紝鏃犳硶姝ｅ父鐐圭伀",
          state: [{
            name: "U鐩�",
            tip: "鎻掑叆绗旇�版湰鐢佃剳涓�鑳借幏寰楀唴閮ㄦ暟鎹�",
            desc: "涓�涓�鎵撶伀鏈哄�栧舰鐨� U 鐩�",
            preClue: ["#鏆楁牸-3"]
          }],
          nodes: [{
            name: "鏆楁牸",
            desc: "鍦ㄥ簳閮ㄦ湁涓�闅愯棌鐨勬殫鏍�",
            preClue: "#澶囧繕褰�",
            type: "knock",
            data: {
              knockCount: 1,
              clue: "#鏆楁牸-{0}",
              stopClue: "#鏆楁牸-3",
              audio: "鐐瑰嚮1"
            }
          }],
          interact: [{
            type: "use",
            target: "绗旇�版湰鐢佃剳",
            preClue: "#鏆楁牸-3",
            clue: "#U鐩�>绗旇�版湰鐢佃剳",
            params: {
              isOnce: !0
            }
          }]
        }]
      }]
    }]
  }
  , Bs = {
    name: "澶滆�嗕华",
    key: "澶滆�嗕华",
    preClue: "#搴婂ご鏌滈攣",
    type: "switch",
    data: {
      independent: !0,
      triggerType: "click",
      clue: "*澶滆�嗕华",
      preClue: "-#鐢甸噺-0",
      openBorderColor: "#00ff00"
    },
    nodes: [{
      name: "鐢甸噺",
      key: "鐢甸噺",
      type: "timer",
      preClue: "*澶滆�嗕华",
      data: {
        time: 4 * 60,
        autoAdd: !0,
        startClue: "*澶滆�嗕华",
        stopClue: "-*澶滆�嗕华",
        overClue: ["@Switch-澶滆�嗕华?isOpen=false", "#鐢甸噺-0"]
      }
    }, {
      name: "鐢甸噺-闅愯棌鑺傜偣",
      key: "鐢甸噺闅愯棌鑺傜偣",
      type: "timer",
      preClue: "*澶滆�嗕华",
      data: {
        time: 15,
        autoAdd: !0,
        independent: !0,
        stealthUntilClue: "#鐢甸噺-闅愯棌鑺傜偣",
        startClue: ["*榛戞殫", "#鐢甸噺-0"],
        stopClue: "*澶滆�嗕华|-#鐢甸噺-0",
        overClue: "#澶辫触-澶滆�嗕华"
      }
    }]
  }