# from sklearn.impute import KNNImputer

# ## Target - Purchases in the first six months
# r_df = df.copy()

# X_r = r_df['Total énergie soutirée (Wh)']
# y_r = r_df['lifetime_value']


# X_train_r = X_r[:4000]
# y_train_r = y_r[:4000]

# X_test_r = X_r[1000:]
# y_test_r = y_r[1000:]

# imputer = KNNImputer(n_neighbors=5, weights="uniform")
# imputer.fit(X_train_r)
# X_train_k = imputer.transform(X_train_r)
# X_test_k = imputer.transform(X_test_r)

# y_train_k = y_train_r.copy()
# y_test_k = y_test_r.copy()


# imputer = KNNImputer(n_neighbors=5, weights="uniform")
# imputer.fit(X_train_r)
# X_train_k = imputer.transform(X_train_r)
# X_test_k = imputer.transform(X_test_r)

# y_train_k = y_train_r.copy()
# y_test_k = y_test_r.copy()