class AlgorithmDQN:
    judge = JUDGE()

    policy_net = DQN(WIDTH, HEIGHT, ACTION_SIZE).to(DEVICE)
    if os.path.exists(DQN_MODEL_PATH):
        policy_net.load_state_dict(torch.load(DQN_MODEL_PATH))
        print("[*] policy_net load finish!")
    target_net = DQN(WIDTH, HEIGHT, ACTION_SIZE).to(DEVICE)
    target_net.load_state_dict(policy_net.state_dict())
    target_net.eval()
    # print("[*] target_net", target_net.eval())
    if os.path.exists(DQN_STORE_PATH):
        judge.replay_buffer = pickle.load(open(DQN_STORE_PATH, 'rb'))
        print("[*] REPLAY_BUFFER load finish! len:", len(judge.replay_buffer))

    plt_step_list = []
    plt_step = 0
    plt_reward = []
    plt.ion()
    plt.figure(1, figsize=(10, 1))

    plt.plot(plt_step_list, plt_reward, color="orange")
    plt.pause(3)

    # DQN init
    paused = True
    paused = pause_game(paused)
    emergence_break = 0  # 用于防止错误训练数据扰乱神经网络
    target_step = 0

    # 开始脚本
    handld_top()
    init_init()

    for episode in range(EPISODES):
        done = 0
        total_reward = 0
        avg_step = 1
        stop = 0

        last_time = time.time()
        init_time = time.time()

        blood_window_gray_first = cv2.cvtColor(grab_screen(blood_window), cv2.COLOR_BGR2GRAY)
        power_window_gray = cv2.cvtColor(grab_screen(power_window), cv2.COLOR_BGR2GRAY)
        judge.all_blood = self_blood_number(blood_window_gray_first)
        judge.all_power = self_power_number(power_window_gray, power_window)
        choose_time = time.time()

        while True:

            # step1：先获取环境
            first_screen_grey = cv2.cvtColor(grab_screen(main_window), cv2.COLOR_BGR2GRAY)  # TODO 取差值
            # second_screen_grey = cv2.cvtColor(grab_screen(main_window), cv2.COLOR_BGR2GRAY)
            blood_window_gray = cv2.cvtColor(grab_screen(blood_window), cv2.COLOR_BGR2GRAY)
            power_window_gray = cv2.cvtColor(grab_screen(power_window), cv2.COLOR_BGR2GRAY)
            # screen_grey = second_screen_grey - first_screen_grey
            station = cv2.resize(first_screen_grey, (WIDTH, HEIGHT))
            station = np.array(station).reshape(-1, 1, WIDTH, HEIGHT)
            self_blood = self_blood_number(blood_window_gray)
            self_power = self_power_number(power_window_gray, power_window)
            # print(station.shape)

            target_step += 1

            # step2：执行动作
            # print("[*] station:", station)
            action = judge.choose_action(policy_net, station, time.time() - choose_time)
            handld_top()
            take_action(action)

            # step3：再获取环境
            third_screen_grey = cv2.cvtColor(grab_screen(main_window), cv2.COLOR_BGR2GRAY)
            next_blood_window_gray = cv2.cvtColor(grab_screen(blood_window), cv2.COLOR_BGR2GRAY)
            next_power_window_gray = cv2.cvtColor(grab_screen(power_window), cv2.COLOR_BGR2GRAY)
            # next_screen_grey = third_screen_grey - second_screen_grey
            next_station = cv2.resize(third_screen_grey, (WIDTH, HEIGHT))
            cv2.imshow("window_main", next_station)
            cv2.moveWindow("window_main", 1100, 540)
            if cv2.waitKey(1) & 0xFF == ord('a'):
                pass
            next_station = np.array(next_station).reshape(-1, 1, WIDTH, HEIGHT)
            next_self_blood = self_blood_number(next_blood_window_gray)
            next_self_power = self_power_number(next_power_window_gray, power_window)  #

            # 获得奖励
            init_time, reward, done, stop, emergence_break = \
                judge.action_judge(init_time, next_self_blood, next_self_power, action, stop, emergence_break)

            # 存储到经验池
            judge.store_data(station, action, reward, next_station)

            if len(judge.replay_buffer) > STORE_SIZE:
                num_step += 1  # 用于保存参数图像
                judge.train_network(policy_net, target_net, num_step)
            if target_step % UPDATE_STEP == 0:
                target_net.load_state_dict(policy_net.state_dict())

            total_reward += reward
            avg_step += 1

            paused = pause_game(paused)

            # 建议每次相应时间<0.25即一秒钟4个操作，否则会感觉卡卡的，耗时按键模拟除外
            print('once reward {}, second{}.'.format(total_reward, time.time() - last_time))
            last_time = time.time()

            if done == 1:
                blood_window_gray_done = cv2.cvtColor(grab_screen(blood_window), cv2.COLOR_BGR2GRAY)
                self_blood_done = self_blood_number(blood_window_gray_done)
                if self_blood_done == 0:
                    judge.choose_action_time = time.time() - choose_time
                    break

        if episode % 2 == 0:
            torch.save(policy_net.state_dict(), DQN_MODEL_PATH)
            if os.path.exists(DQN_STORE_PATH):
                os.remove(DQN_STORE_PATH)
            pickle.dump(judge.replay_buffer, open(DQN_STORE_PATH, 'wb'))
        plt_step_list.append(plt_step)
        plt_step += 1
        plt_reward.append(total_reward / avg_step)
        plt.plot(plt_step_list, plt_reward, color="orange")
        plt.pause(0.1)
        print("[*] Epoch: ", episode, "Store: ", len(judge.replay_buffer), "Reward: ", total_reward / avg_step,
              "Time: ", judge.choose_action_time)

        time.sleep(12)
        handld_top()
        init_start()
