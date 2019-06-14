import argparse
from shutil import copyfile

from model import matplot_helper
from model.paper2vec_trainer import Paper2VecTrainer

parser = argparse.ArgumentParser()

parser.add_argument('data_dir', default='raw_data', type=str, nargs='?', help='directory for data')
parser.add_argument('model_dir', default='data', type=str, nargs='?', help='directory for data data')

# args for building corpus
parser.add_argument('-d', '--max_dictionary_words', default=30000, type=int, nargs='?')
parser.add_argument('-t', '--phrase_threshold', default=1000, type=int, nargs='?')

# args for training / clustering
parser.add_argument('-m', '--train_model', default='skipgram', type=str, nargs='?',
                    help='data for training word representation')
parser.add_argument('-w', '--word_dim', default=75, type=int, nargs='?', help='dimensions for word representation')
parser.add_argument('-i', '--min_count', default=10, type=int, nargs='?', help='minimal number of word occurences')
parser.add_argument('-p', '--paper_dim', default=3, type=int, nargs='?', help='dimensions for paper representation')
parser.add_argument('-x', '--perplexity', default=25, type=int, nargs='?', help='perplexity param for t-SNE')
parser.add_argument('-c', '--clusters', default=9, type=int, nargs='?', help='number of clusters to be divided')

args = parser.parse_args()


def main(args):
	p2v = Paper2VecTrainer(word_dim=args.word_dim, data_dir=args.data_dir, model_dir=args.model_dir)

	print('\nStep 1: Replaces rare words with UNK token to build a suitable size of dictionary.')

	p2v.add_dictionary_from_file('CVPR2016/corpus.txt')
	p2v.add_dictionary_from_file('CVPR2017/corpus.txt')
	p2v.add_dictionary_from_file('CVPR2018/corpus.txt')
	p2v.add_dictionary_from_file('CVPR2019/corpus.txt')
	# p2v.add_dictionary_from_file('ICCV2015/corpus.txt')
	# p2v.add_dictionary_from_file('ICCV2017/corpus.txt')
	p2v.build_dictionary(args.max_dictionary_words)

	print('Check most 20 common words:', p2v.count[:20])

	print('\nStep 2: Detects phrases by their appearance frequency. Then re-build a new corpus.')
	p2v.detect_phrases(args.phrase_threshold)

	p2v.create_corpus_with_phrases('corpus.txt')
	p2v.convert_text_with_phrases('CVPR2019/abstract.txt', 'abstract.txt')
	copyfile(args.data_dir + '/CVPR2019/paper_info.txt', args.data_dir + '/paper_info.txt')

	p2v.create_label('abstract.txt', 'abstract_label.txt')  # don't use this label for now though...

	print('\nStep 3: Train word representation with fasttext.')
	p2v.train_words_model('corpus.txt', 'fasttext_model', model=args.train_model, min_count=args.min_count)

	print('Checking result. Find similar words for...')
	print('[deep_learning]', p2v.get_most_similar_words('deep_learning', 12))
	print('[light_field]', p2v.get_most_similar_words('light_field', 12))
	print('[feature]', p2v.get_most_similar_words('feature', 12))
	print('[super_resolution]', p2v.get_most_similar_words('super_resolution', 12))
	print('[object_detection]', p2v.get_most_similar_words('object_detection', 12))

	print('\nStep 4: Build paper representation vectors with fasttext.')
	p2v.build_paper_vectors('abstract.txt')

	print('\nStep 5: Reduce dimensions and then apply k-means clustering.')
	p2v.reduce_paper_vectors_dim(args.paper_dim, perplexity=args.perplexity)
	p2v.clustering_papers(clusters=args.clusters)
	for i in range(args.clusters):
		print('cluster[%d] keywords:' % i, p2v.cluster_abstract_freq[i][:15])
	matplot_helper.plot_with_labels(p2v.paper_vectors, filename=args.data_dir + '/papers.png',
	                                markers=p2v.paper_cluster_ids, perplexity=args.perplexity)

	p2v.save_paper_vectors()

	print('\nStep (6): Reduce dimensions to 2D and visualize it.')
	p2v.reduce_paper_vectors_dim(2, perplexity=args.perplexity)
	p2v.clustering_papers(clusters=args.clusters)
	matplot_helper.plot_with_labels(p2v.paper_vectors, filename=args.data_dir + '/papers_2d.png',
	                                markers=p2v.paper_cluster_ids, perplexity=args.perplexity)


if __name__ == '__main__':
	main(args)
