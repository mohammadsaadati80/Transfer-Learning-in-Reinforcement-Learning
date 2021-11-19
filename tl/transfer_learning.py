from stable_baselines3.common.monitor import Monitor
from tl.model_evaluation import *
from tl.plot_utils import *
from model_generator import *

def transfer_execute(source_env,
                     target_env,
                     algo='DDPG',
                     policy_name='MlpPolicy',
                     step_number = 10000,
                     step_number_small = 10000,
                     callback_check_freq = 200,
                     moving_window = 50,
                     log_dir_w_TL = "/tmp/gym/w_tl/",
                     log_dir_wo_TL = "/tmp/gym/wo_tl/"
                     ):
    print(">>Executing with algorithm " + algo + "...")

    os.makedirs(log_dir_w_TL, exist_ok=True)
    os.makedirs(log_dir_wo_TL, exist_ok=True)

    source_model = get_model(policy_name, source_env, verbose=2, algo=algo)

    print(">>[Source] Evaluate un-trained agent:")
    evaluate(source_model, 100)

    source_model.learn(total_timesteps=step_number)
    source_model.save("./source_model_trained")
    print(">>[Source] Evaluate trained agent:")
    evaluate(source_model, 100)

    # sample an observation from the environment
    obs = source_model.env.observation_space.sample()

    # Check prediction before saving
    print("pre saved", source_model.predict(obs, deterministic=True))

    del source_model  # delete trained model to demonstrate loading

    ##### LOAD source model and train with target domain
    target_model = load_model(algo=algo, src="./source_model_trained")
    # Check that the prediction is the same after loading (for the same observation)
    print("loaded", target_model.predict(obs, deterministic=True))

    # as the environment is not serializable, we need to set a new instance of the environment
    target_env_monitor_with_TL = Monitor(target_env, log_dir_w_TL)
    target_model.set_env(target_env_monitor_with_TL)
    callback_w_TL = SaveOnBestTrainingRewardCallback(check_freq=callback_check_freq, log_dir=log_dir_w_TL)
    # and continue training
    target_model.learn(step_number_small, callback=callback_w_TL)
    print(">>[Target] Evaluate trained agent using source model:")
    evaluate(target_model, 100)

    #### Train target model without transfer
    target_env_monitor = Monitor(target_env, log_dir_wo_TL)
    callback = SaveOnBestTrainingRewardCallback(check_freq=callback_check_freq, log_dir=log_dir_wo_TL)
    target_model_wo_TL = get_model(policy_name, target_env_monitor, verbose=2, algo='A2C')
    target_model_wo_TL.learn(total_timesteps=step_number_small, callback=callback)
    print(">>[Target] Evaluate trained agent without TL:")
    evaluate(target_model_wo_TL, 100)