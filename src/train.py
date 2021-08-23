import os

import numpy as np
import torch
import torch.multiprocessing
import torch.nn as nn
import torch.nn.functional as F
from torch.utils import data
from tqdm import tqdm

import augmentation
from argparser import parse_arguments
from config import *
from dataset import Dataset
from model import DeepPunctuation, DeepPunctuationCRF


class WeightedFocalLoss(nn.Module):
    "Non weighted version of Focal Loss"
    def __init__(self, alpha=.25, gamma=2):
        super(WeightedFocalLoss, self).__init__()
        self.alpha = torch.tensor([alpha, 1-alpha]).cuda()
        self.gamma = gamma

    def forward(self, inputs, targets):
        BCE_loss = F.binary_cross_entropy_with_logits(inputs, targets, reduction='none')
        targets = targets.type(torch.long)
        at = self.alpha.gather(0, targets.data.view(-1))
        pt = torch.exp(-BCE_loss)
        F_loss = at*(1-pt)**self.gamma * BCE_loss
        return F_loss.mean()

torch.multiprocessing.set_sharing_strategy(
    'file_system'
)  # https://github.com/pytorch/pytorch/issues/11201

args = parse_arguments()

# for reproducibility
torch.manual_seed(args.seed)
torch.backends.cudnn.deterministic = True
torch.backends.cudnn.benchmark = False
np.random.seed(args.seed)

# tokenizer
tokenizer = MODELS[args.pretrained_model][1].from_pretrained(args.pretrained_model)
augmentation.tokenizer = tokenizer
augmentation.sub_style = args.sub_style
augmentation.alpha_sub = args.alpha_sub
augmentation.alpha_del = args.alpha_del
token_style = MODELS[args.pretrained_model][3]
ar = args.augment_rate
sequence_len = args.sequence_length
aug_type = args.augment_type

# Datasets
if args.language == 'polish':
    train_set = Dataset(
        os.path.join(args.data_path, 'pl/train'),
        tokenizer=tokenizer,
        sequence_len=sequence_len,
        token_style=token_style,
        is_train=True,
        augment_rate=ar,
        augment_type=aug_type,
    )
    val_set = Dataset(
        os.path.join(args.data_path, 'pl/dev'),
        tokenizer=tokenizer,
        sequence_len=sequence_len,
        token_style=token_style,
        is_train=False,
    )
    test_set_ref = Dataset(
        os.path.join(args.data_path, 'pl/test'),
        tokenizer=tokenizer,
        sequence_len=sequence_len,
        token_style=token_style,
        is_train=False,
    )
    test_set_asr = Dataset(
        os.path.join(args.data_path, 'pl/test'),
        tokenizer=tokenizer,
        sequence_len=sequence_len,
        token_style=token_style,
        is_train=False,
    )
    test_set = [val_set, test_set_ref, test_set_asr]
if args.language == 'poleval':
    train_set = Dataset(
        os.path.join(args.data_path, 'poleval/train'),
        tokenizer=tokenizer,
        sequence_len=sequence_len,
        token_style=token_style,
        is_train=True,
        augment_rate=ar,
        augment_type=aug_type,
    )
    val_set = Dataset(
        os.path.join(args.data_path, 'poleval/dev'),
        tokenizer=tokenizer,
        sequence_len=sequence_len,
        token_style=token_style,
        is_train=False,
    )
    test_set_ref = Dataset(
        os.path.join(args.data_path, 'poleval/test'),
        tokenizer=tokenizer,
        sequence_len=sequence_len,
        token_style=token_style,
        is_train=False,
    )
    test_set_asr = Dataset(
        os.path.join(args.data_path, 'poleval/test'),
        tokenizer=tokenizer,
        sequence_len=sequence_len,
        token_style=token_style,
        is_train=False,
    )
    test_set = [val_set, test_set_ref, test_set_asr]
elif args.language == 'english':
    train_set = Dataset(
        os.path.join(args.data_path, 'en/train2012'),
        tokenizer=tokenizer,
        sequence_len=sequence_len,
        token_style=token_style,
        is_train=True,
        augment_rate=ar,
        augment_type=aug_type,
    )
    val_set = Dataset(
        os.path.join(args.data_path, 'en/dev2012'),
        tokenizer=tokenizer,
        sequence_len=sequence_len,
        token_style=token_style,
        is_train=False,
    )
    test_set_ref = Dataset(
        os.path.join(args.data_path, 'en/test2011'),
        tokenizer=tokenizer,
        sequence_len=sequence_len,
        token_style=token_style,
        is_train=False,
    )
    test_set_asr = Dataset(
        os.path.join(args.data_path, 'en/test2011asr'),
        tokenizer=tokenizer,
        sequence_len=sequence_len,
        token_style=token_style,
        is_train=False,
    )
    test_set = [val_set, test_set_ref, test_set_asr]
elif args.language == 'bangla':
    train_set = Dataset(
        os.path.join(args.data_path, 'bn/train'),
        tokenizer=tokenizer,
        sequence_len=sequence_len,
        token_style=token_style,
        is_train=True,
        augment_rate=ar,
        augment_type=aug_type,
    )
    val_set = Dataset(
        os.path.join(args.data_path, 'bn/dev'),
        tokenizer=tokenizer,
        sequence_len=sequence_len,
        token_style=token_style,
        is_train=False,
    )
    test_set_news = Dataset(
        os.path.join(args.data_path, 'bn/test_news'),
        tokenizer=tokenizer,
        sequence_len=sequence_len,
        token_style=token_style,
        is_train=False,
    )
    test_set_ref = Dataset(
        os.path.join(args.data_path, 'bn/test_ref'),
        tokenizer=tokenizer,
        sequence_len=sequence_len,
        token_style=token_style,
        is_train=False,
    )
    test_set_asr = Dataset(
        os.path.join(args.data_path, 'bn/test_asr'),
        tokenizer=tokenizer,
        sequence_len=sequence_len,
        token_style=token_style,
        is_train=False,
    )
    test_set = [val_set, test_set_news, test_set_ref, test_set_asr]
elif args.language == 'english-bangla':
    train_set = Dataset(
        [
            os.path.join(args.data_path, 'en/train2012'),
            os.path.join(args.data_path, 'bn/train_bn'),
        ],
        tokenizer=tokenizer,
        sequence_len=sequence_len,
        token_style=token_style,
        is_train=True,
        augment_rate=ar,
        augment_type=aug_type,
    )
    val_set = Dataset(
        [
            os.path.join(args.data_path, 'en/dev2012'),
            os.path.join(args.data_path, 'bn/dev_bn'),
        ],
        tokenizer=tokenizer,
        sequence_len=sequence_len,
        token_style=token_style,
        is_train=False,
    )
    test_set_ref = Dataset(
        os.path.join(args.data_path, 'en/test2011'),
        tokenizer=tokenizer,
        sequence_len=sequence_len,
        token_style=token_style,
        is_train=False,
    )
    test_set_asr = Dataset(
        os.path.join(args.data_path, 'en/test2011asr'),
        tokenizer=tokenizer,
        sequence_len=sequence_len,
        token_style=token_style,
        is_train=False,
    )
    test_set_news = Dataset(
        os.path.join(args.data_path, 'bn/test_news'),
        tokenizer=tokenizer,
        sequence_len=sequence_len,
        token_style=token_style,
        is_train=False,
    )
    test_bn_ref = Dataset(
        os.path.join(args.data_path, 'bn/test_ref'),
        tokenizer=tokenizer,
        sequence_len=sequence_len,
        token_style=token_style,
        is_train=False,
    )
    test_bn_asr = Dataset(
        os.path.join(args.data_path, 'bn/test_asr'),
        tokenizer=tokenizer,
        sequence_len=sequence_len,
        token_style=token_style,
        is_train=False,
    )
    test_set = [
        val_set,
        test_set_ref,
        test_set_asr,
        test_set_news,
        test_bn_ref,
        test_bn_asr,
    ]
else:
    raise ValueError('Incorrect language argument for Dataset')

# Data Loaders
data_loader_params = {'batch_size': args.batch_size, 'shuffle': True, 'num_workers': 1}
train_loader = torch.utils.data.DataLoader(train_set, **data_loader_params)
val_loader = torch.utils.data.DataLoader(val_set, **data_loader_params)
test_loaders = [torch.utils.data.DataLoader(x, **data_loader_params) for x in test_set]

# logs
os.makedirs(args.save_path, exist_ok=True)
model_save_path = os.path.join(args.save_path, 'weights.pt')
log_path = os.path.join(args.save_path, args.name + '_logs.txt')


# Model
device = torch.device('cuda' if (args.cuda and torch.cuda.is_available()) else 'cpu')
if args.use_crf:
    deep_punctuation = DeepPunctuationCRF(
        args.pretrained_model, freeze_bert=args.freeze_bert, lstm_dim=args.lstm_dim
    )
else:
    deep_punctuation = DeepPunctuation(
        args.pretrained_model, freeze_bert=args.freeze_bert, lstm_dim=args.lstm_dim
    )
deep_punctuation.to(device)
criterion = WeightedFocalLoss()
optimizer = torch.optim.Adam(
    deep_punctuation.parameters(), lr=args.lr, weight_decay=args.decay
)


def validate(data_loader):
    """
    :return: validation accuracy, validation loss
    """
    num_iteration = 0
    deep_punctuation.eval()
    correct = 0
    total = 0
    val_loss = 0
    with torch.no_grad():
        for x, y, att, y_mask in tqdm(data_loader, desc='eval'):
            x, y, att, y_mask = (
                x.to(device),
                y.to(device),
                att.to(device),
                y_mask.to(device),
            )
            y_mask = y_mask.view(-1)
            if args.use_crf:
                y_predict = deep_punctuation(x, att, y)
                loss = deep_punctuation.log_likelihood(x, att, y)
                y_predict = y_predict.view(-1)
                y = y.view(-1)
            else:
                y_predict = deep_punctuation(x, att)
                y = y.view(-1)
                y_predict = y_predict.view(-1, y_predict.shape[2])
                loss = criterion(y_predict, y)
                y_predict = torch.argmax(y_predict, dim=1).view(-1)
            val_loss += loss.item()
            num_iteration += 1
            y_mask = y_mask.view(-1)
            correct += torch.sum(y_mask * (y_predict == y).long()).item()
            total += torch.sum(y_mask).item()
    return correct / total, val_loss / num_iteration


def test(data_loader):
    """
    :return: precision[numpy array], recall[numpy array], f1 score [numpy array], accuracy, confusion matrix
    """
    num_iteration = 0
    deep_punctuation.eval()
    # +1 for overall result
    tp = np.zeros(1 + len(punctuation_dict), dtype=np.int)
    fp = np.zeros(1 + len(punctuation_dict), dtype=np.int)
    fn = np.zeros(1 + len(punctuation_dict), dtype=np.int)
    cm = np.zeros((len(punctuation_dict), len(punctuation_dict)), dtype=np.int)
    correct = 0
    total = 0
    with torch.no_grad():
        for x, y, att, y_mask in tqdm(data_loader, desc='test'):
            x, y, att, y_mask = (
                x.to(device),
                y.to(device),
                att.to(device),
                y_mask.to(device),
            )
            y_mask = y_mask.view(-1)
            if args.use_crf:
                y_predict = deep_punctuation(x, att, y)
                y_predict = y_predict.view(-1)
                y = y.view(-1)
            else:
                y_predict = deep_punctuation(x, att)
                y = y.view(-1)
                y_predict = y_predict.view(-1, y_predict.shape[2])
                y_predict = torch.argmax(y_predict, dim=1).view(-1)
            num_iteration += 1
            y_mask = y_mask.view(-1)
            correct += torch.sum(y_mask * (y_predict == y).long()).item()
            total += torch.sum(y_mask).item()
            for i in range(y.shape[0]):
                if y_mask[i] == 0:
                    # we can ignore this because we know there won't be any punctuation in this position
                    # since we created this position due to padding or sub-word tokenization
                    continue
                cor = y[i]
                prd = y_predict[i]
                if cor == prd:
                    tp[cor] += 1
                else:
                    fn[cor] += 1
                    fp[prd] += 1
                cm[cor][prd] += 1
    # ignore first index which is for no punctuation
    tp[-1] = np.sum(tp[1:])
    fp[-1] = np.sum(fp[1:])
    fn[-1] = np.sum(fn[1:])
    precision = tp / (tp + fp)
    recall = tp / (tp + fn)
    f1 = 2 * precision * recall / (precision + recall)

    return precision, recall, f1, correct / total, cm


def train():
    with open(log_path, 'a') as f:
        f.write(str(args) + '\n')
    best_val_acc = 0
    for epoch in range(args.epoch):
        train_loss = 0.0
        train_iteration = 0
        correct = 0
        total = 0
        deep_punctuation.train()
        for x, y, att, y_mask in tqdm(train_loader, desc='train'):
            x, y, att, y_mask = (
                x.to(device),
                y.to(device),
                att.to(device),
                y_mask.to(device),
            )
            y_mask = y_mask.view(-1)
            if args.use_crf:
                loss = deep_punctuation.log_likelihood(x, att, y)
                # y_predict = deep_punctuation(x, att, y)
                # y_predict = y_predict.view(-1)
                y = y.view(-1)
            else:
                y_predict = deep_punctuation(x, att)
                y_predict = y_predict.view(-1, y_predict.shape[2])
                y = y.view(-1)
                loss = criterion(y_predict, y)
                y_predict = torch.argmax(y_predict, dim=1).view(-1)

                correct += torch.sum(y_mask * (y_predict == y).long()).item()

            optimizer.zero_grad()
            train_loss += loss.item()
            train_iteration += 1
            loss.backward()

            if args.gradient_clip > 0:
                torch.nn.utils.clip_grad_norm_(
                    deep_punctuation.parameters(), args.gradient_clip
                )
            optimizer.step()

            y_mask = y_mask.view(-1)

            total += torch.sum(y_mask).item()

        train_loss /= train_iteration
        log = 'epoch: {}, Train loss: {}, Train accuracy: {}'.format(
            epoch, train_loss, correct / total
        )
        with open(log_path, 'a') as f:
            f.write(log + '\n')
        print(log)

        val_acc, val_loss = validate(val_loader)
        log = 'epoch: {}, Val loss: {}, Val accuracy: {}'.format(
            epoch, val_loss, val_acc
        )
        with open(log_path, 'a') as f:
            f.write(log + '\n')
        print(log)
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(deep_punctuation.state_dict(), model_save_path)

    print('Best validation Acc:', best_val_acc)
    deep_punctuation.load_state_dict(torch.load(model_save_path))
    for loader in test_loaders:
        precision, recall, f1, accuracy, cm = test(loader)
        log = (
            'Precision: '
            + str(precision)
            + '\n'
            + 'Recall: '
            + str(recall)
            + '\n'
            + 'F1 score: '
            + str(f1)
            + '\n'
            + 'Accuracy:'
            + str(accuracy)
            + '\n'
            + 'Confusion Matrix'
            + str(cm)
            + '\n'
        )
        print(log)
        with open(log_path, 'a') as f:
            f.write(log)
        log_text = ''
        for i in range(1, 5):
            log_text += (
                str(precision[i] * 100)
                + ' '
                + str(recall[i] * 100)
                + ' '
                + str(f1[i] * 100)
                + ' '
            )
        with open(log_path, 'a') as f:
            f.write(log_text[:-1] + '\n\n')


if __name__ == '__main__':
    train()
